package cimgen

import (
	"fmt"
	"io"
	"strings"

	cimgo "github.com/sogno-platform/cimgen/cimgostructs"
	"github.com/sogno-platform/cimgen/cimgoxml"
)

func EncodeProfile(w io.Writer, cimData *cimgo.CIMDataset) error {
	enc := cimgoxml.NewEncoder(w)
	enc.Indent("", "  ")

	start := cimgoxml.StartElement{
		Name: cimgoxml.Name{Local: "rdf:RDF"},
		Attr: []cimgoxml.Attr{
			{Name: cimgoxml.Name{Local: "xmlns:rdf"}, Value: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
			{Name: cimgoxml.Name{Local: "xmlns:cim"}, Value: "http://iec.ch/TC57/2013/CIM-schema-cim16#"}},
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
