package cimgo

import (
	"encoding/xml"
	"fmt"
	"io"
	"strings"

	"github.com/sogno-platform/cimgen/cimgostructs"
	"github.com/sogno-platform/cimgen/cimgoxml"
)

func EncodeProfile(w io.Writer, cimData *cimgostructs.CIMElementList) error {
	enc := cimgoxml.NewEncoder(w)
	enc.Indent("", "  ")

	start := xml.StartElement{
		Name: xml.Name{Local: "rdf:RDF"},
		Attr: []xml.Attr{
			{Name: xml.Name{Local: "xmlns:rdf"}, Value: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
			{Name: xml.Name{Local: "xmlns:cim"}, Value: "http://iec.ch/TC57/2013/CIM-schema-cim16#"}},
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

	return nil
}
