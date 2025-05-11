package cimgen

import (
	"encoding/xml"
	"errors"
	"io"
	"log/slog"
	"strings"
)

const (
	attrPrefix = "@"
	textPrefix = "_"
)

var (
	ErrInvalidDocument = errors.New("invalid document")
	ErrInvalidRoot     = errors.New("invalid root element")
)

type node struct {
	Parent      *node
	Value       map[string]interface{}
	Attrs       []xml.Attr
	Label       string
	Space       string
	Text        string
	HasElements bool
}

// DecodeToMap creates a map from an XML document.
// It does not support mixed XML content.
func DecodeToMap(r io.Reader) (map[string]interface{}, error) {
	dec := xml.NewDecoder(r)
	n := &node{}
	stack := make([]*node, 0)

	for {
		token, err := dec.RawToken()
		if err != nil && err != io.EOF {
			return nil, err
		}

		if err == io.EOF {
			slog.Debug("Reached end of file")
			return n.Value, nil
		}

		switch t := token.(type) {
		case xml.StartElement:
			processStartElement(&t, &n, &stack)
		case xml.EndElement:
			n = processEndElement(&t, &stack)

			if len(stack) == 0 {
				return n.Value, nil
			} else {
				setNodeValue(n)
				n = n.Parent
			}

		case xml.CharData:
			if str := strings.TrimSpace(string(t)); len(str) > 0 {
				slog.Debug("Found", "CharData", str)

				if len(stack) > 0 {
					stack[len(stack)-1].Text = str
				} else {
					return nil, ErrInvalidRoot
				}
			}
		case xml.Comment:
			slog.Debug("Found", "Comment", string(t))
		case xml.Directive:
			slog.Debug("Found", "Directive", string(t))
		case xml.ProcInst:
			slog.Debug("Found", "ProcInst target", t.Target, "ProcInst inst", string(t.Inst))
		}
	}
}

func processStartElement(tok *xml.StartElement, n **node, stack *[]*node) {
	// remove parent classes introduced by CIM class hierarchy
	labelParts := strings.Split(tok.Name.Local, ".")
	labelEnd := labelParts[len(labelParts)-1]
	spacedLabel := tok.Name.Space + ":" + labelEnd

	slog.Debug("Found", "StartElement", spacedLabel)

	if len(tok.Attr) > 0 {
		for _, attr := range tok.Attr {
			slog.Debug("Found", "attributeName", attr.Name.Local, "attributeValue", attr.Value)
		}
	}

	*n = &node{
		Label:  spacedLabel,
		Space:  tok.Name.Space,
		Parent: *n,
		Value:  map[string]interface{}{spacedLabel: map[string]interface{}{}},
		Attrs:  tok.Attr,
	}

	setAttributes(*n, tok, attrPrefix)
	*stack = append(*stack, *n)

	if (*n).Parent != nil {
		(*n).Parent.HasElements = true
	}
}

func processEndElement(tok *xml.EndElement, stack *[]*node) (n *node) {
	// remove parent classes introduced by CIM class hierarchy
	labelParts := strings.Split(tok.Name.Local, ".")
	labelEnd := labelParts[len(labelParts)-1]
	spacedLabel := tok.Name.Space + ":" + labelEnd

	slog.Debug("Found", "EndElement", spacedLabel)

	length := len(*stack)
	*stack, n = (*stack)[:length-1], (*stack)[length-1]

	// NOTE: mixed content is not supported!
	if !n.HasElements && n.Text != "" {
		if len(n.Attrs) > 0 {
			m := n.Value[n.Label].(map[string]interface{})
			m[textPrefix] = n.Text
		} else {
			n.Value[n.Label] = n.Text
		}
	}

	return n
}

func setNodeValue(n *node) {
	if parentValue, ok := n.Parent.Value[n.Parent.Label]; ok {
		parentValueMap := parentValue.(map[string]interface{})
		if value, ok := parentValueMap[n.Label]; ok {

			switch item := value.(type) {
			case string:
				// node with string value exists in parent node, replace with string slice

				if nodeValue, ok := n.Value[n.Label].(map[string]interface{}); ok {
					parentValueMap[n.Label] = []interface{}{item, nodeValue}
				} else {
					parentValueMap[n.Label] = []string{item, n.Value[n.Label].(string)}
				}
			case []string:
				if nodeValue, ok := n.Value[n.Label].(map[string]interface{}); ok {
					s := make([]interface{}, len(item))
					for i, v := range item {
						s[i] = v
					}
					parentValueMap[n.Label] = append(s, nodeValue)
				} else {
					parentValueMap[n.Label] = append(item, n.Value[n.Label].(string))
				}
			case map[string]interface{}:
				// node with map value exists in parent node, replace with map slice
				if _, ok := n.Value[n.Label].(map[string]interface{}); ok {
					vm := getMap(n)
					if vm != nil {
						parentValueMap[n.Label] = []map[string]interface{}{item, vm}
					}
				} else {
					parentValueMap[n.Label] = []interface{}{item, n.Value[n.Label]}
				}
			case []map[string]interface{}:
				if _, ok := n.Value[n.Label].(map[string]interface{}); ok {
					vm := getMap(n)
					if vm != nil {
						parentValueMap[n.Label] = append(item, vm)
					}
				} else {
					s := make([]interface{}, len(item))
					for i, v := range item {
						s[i] = v
					}
					parentValueMap[n.Label] = append(s, n.Value[n.Label])
				}
			case []interface{}:
				if _, ok := n.Value[n.Label].(map[string]interface{}); ok {
					vm := getMap(n)
					if vm != nil {
						parentValueMap[n.Label] = append(item, vm)
					}
				} else {
					parentValueMap[n.Label] = append(item, n.Value[n.Label])
				}
			}
		} else {
			// current node does not exist in parent node map, insert it
			parentValueMap[n.Label] = n.Value[n.Label]
		}

	} else {
		// map for parent node does not exist, create it and add current node
		n.Parent.Value[n.Parent.Label] = n.Value[n.Label]
	}
}

func getMap(node *node) map[string]interface{} {
	if v, ok := node.Value[node.Label]; ok {
		switch v.(type) {
		case string:
			return map[string]interface{}{node.Label: v}
		case map[string]interface{}:
			return node.Value[node.Label].(map[string]interface{})
		}
	}

	return nil
}

func setAttributes(n *node, tok *xml.StartElement, attrPrefix string) {
	if len(tok.Attr) > 0 {
		m := make(map[string]interface{})
		for _, attr := range tok.Attr {
			spacedLabel := attr.Name.Space + ":" + attr.Name.Local
			m[attrPrefix+spacedLabel] = attr.Value
		}
		n.Value[n.Label] = m
	}
}
