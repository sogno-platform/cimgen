package cimgo

import (
	"cimgo/cimgostructs"
	"cimgo/cimgoxml"
	"encoding/xml"
	"fmt"
	"io"
	"strings"
)

func EncodeProfile(w io.Writer, cimData *cimgostructs.CIMElementList) error {
	if _, err := w.Write([]byte("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n")); err != nil {
		return err
	}

	enc := cimgoxml.NewEncoder(w)
	enc.Indent("", "  ")

	start := xml.StartElement{
		Name: xml.Name{Local: "rdf:RDF"},
		Attr: []xml.Attr{
			{Name: xml.Name{Local: "xmlns:cim"}, Value: cimgostructs.CIMNamespaces["cim"]},
			{Name: xml.Name{Local: "xmlns:rdf"}, Value: cimgostructs.CIMNamespaces["rdf"]},
		},
	}

	if err := enc.EncodeToken(start); err != nil {
		return err
	}

	for _, element := range cimData.Elements {
		label := fmt.Sprintf("%T", element)
		labelParts := strings.Split(label, ".")
		labelEnd := labelParts[len(labelParts)-1]

		fmt.Println("Encoding", labelEnd)

		if err := enc.Encode(element); err != nil {
			return err
		}
	}

	if err := enc.EncodeToken(start.End()); err != nil {
		return err
	}

	if err := enc.Flush(); err != nil {
		return err
	}

	// Add newline at end of file
	if _, err := w.Write([]byte("\n")); err != nil {
		return err
	}

	return nil
}
