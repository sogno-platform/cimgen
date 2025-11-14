package cimgo

type CIMDataset struct {
	Elements map[string]interface{}
}

func NewCIMDataset() *CIMDataset {
	return &CIMDataset{}
}

func (ds *CIMDataset) AddElement(element interface{}) {}
