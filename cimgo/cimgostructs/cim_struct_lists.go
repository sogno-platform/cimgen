package cimgostructs

type CIMElementList struct {
	Elements map[string]interface{}
}

func NewCIMElementList() *CIMElementList {
	return &CIMElementList{}
}

func (ds *CIMElementList) AddElement(element interface{}) {}

var StructMap = map[string]func() interface{}{}
