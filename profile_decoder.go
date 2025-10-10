package cimgen

import (
	"encoding/xml"
	"fmt"
	"io"
	"strings"

	"github.com/sogno-platform/cimgen/cimgo-structs"
)

func DecodeProfile(r io.Reader) (*cimgo.CIMDataset, error) {
	dec := xml.NewDecoder(r)
	cimData := cimgo.NewCIMDataset()

	for {
		token, err := dec.Token()
		if err != nil && err != io.EOF {
			return cimData, err
		}

		if err == io.EOF {
			// slog.Debug("Reached end of file")
			return cimData, nil
		}

		switch t := token.(type) {
		case xml.StartElement:
			labelParts := strings.Split(t.Name.Local, ".")
			labelEnd := labelParts[len(labelParts)-1]
			//spacedLabel := t.Name.Space + ":" + labelEnd

			// slog.Debug("Found", "StartElement", labelEnd)

			fmt.Println("Decode", labelEnd)

			if _, ok := cimgo.StructMap[labelEnd]; ok {
				node := cimgo.StructMap[labelEnd]()

				if err := dec.DecodeElement(node, &t); err != nil {
					panic(err)
				}

				fmt.Println("Decoded", labelEnd, ":", node)
				cimData.AddElement(node)
			} else {
				fmt.Println("Ignoring element", labelEnd)
			}

		case xml.EndElement:
			//labelParts := strings.Split(t.Name.Local, ".")
			//labelEnd := labelParts[len(labelParts)-1]
			// slog.Debug("Found", "EndElement", labelEnd)
		case xml.CharData:
			if str := strings.TrimSpace(string(t)); len(str) > 0 {
				// slog.Debug("Found", "CharData", str)
			}
		case xml.Comment:
			// slog.Debug("Found", "Comment", string(t))
		case xml.Directive:
			// slog.Debug("Found", "Directive", string(t))
		case xml.ProcInst:
			// slog.Debug("Found", "ProcInst target", t.Target, "ProcInst inst", string(t.Inst))
		}
	}
}
