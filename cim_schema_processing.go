package cimgen

import (
	"sort"
	"strings"
)

// postprocess performs various post-processing steps on the CIMSpecification.
func (cimSpec *CIMSpecification) postprocess() {
	cimSpec.determineDataTypes()
	cimSpec.addOriginsOfAttributes()
	cimSpec.setProfilePriorities()

	cimSpec.fixMissingMRIDs()
	cimSpec.renameIdentifiedObjectAttributes()
	cimSpec.reorderOrigins()
	cimSpec.setMainOrigin()

	cimSpec.setHasInverseRole()
	cimSpec.setIsFixedAttributes()
	cimSpec.setMissingNamespaces()
	cimSpec.markUnusedAttributesAndAssociations()
	cimSpec.sortAttributes()

	cimSpec.setDefaultValuesPython()
	cimSpec.setLangTypesPython()
}

// determineDataTypes determines the data types of attributes and marks them as primitive if applicable.
func (cimSpec *CIMSpecification) determineDataTypes() {
	// first, set PrimitiveType for CIMDatatypes
	for _, t := range cimSpec.CIMDatatypes {
		for _, attr := range t.Attributes {
			if attr.Label == "value" {
				t.PrimitiveType = attr.CIMDataType
			}
		}
	}

	// then, determine attribute data types
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.CIMStereotype == "Primitive" || isPrimitiveType(attr.CIMDataType) {
				attr.IsPrimitive = true
				attr.DataType = attr.CIMDataType
			} else if attr.CIMStereotype == "CIMDatatype" || isCIMDatatype(attr.CIMDataType, cimSpec) {
				attr.IsCIMDatatype = true
				attr.DataType = cimSpec.CIMDatatypes[attr.CIMDataType].PrimitiveType
			} else if isEnumType(attr.CIMDataType, cimSpec) {
				attr.IsEnumValue = true
			} else if !attr.IsList && (attr.CIMDataType == DataTypeObject || attr.CIMDataType == "") {
				attr.IsClass = true
				attr.DataType = DataTypeObject
			}
		}
	}
}

// IsPrimitiveType checks if the given type string is a known data type.
func isPrimitiveType(typeStr string) bool {
	switch typeStr {
	case DataTypeString, DataTypeInteger, DataTypeBoolean,
		DataTypeFloat, DataTypeDate,
		DataTypeDateTime:
		return true
	default:
		return false
	}
}

// is CIMDatatype checks if the given type string is a known CIM data type.
func isCIMDatatype(typeStr string, cimSpec *CIMSpecification) bool {
	if _, ok := cimSpec.CIMDatatypes[typeStr]; ok {
		return true
	} else {
		return false
	}
}

// isEnumType checks if the given type string is a known enumeration type.
func isEnumType(typeStr string, cimSpec *CIMSpecification) bool {
	if _, ok := cimSpec.Enums[typeStr]; ok {
		return true
	}
	return false
}

// addOriginsOfAttributes adds the origins of attributes to their parent CIMType's Origins field.
func (cimSpec *CIMSpecification) addOriginsOfAttributes() {
	for _, t := range cimSpec.Types {
		originSet := make(map[string]struct{})
		// add origins of CIMType first
		for _, origin := range t.Origins {
			originSet[origin] = struct{}{}
		}
		// add origins of attributes
		for _, attr := range t.Attributes {
			for _, origin := range attr.Origins {
				originSet[origin] = struct{}{}
			}
		}
		// convert set to slice
		t.Origins = make([]string, 0, len(originSet))
		tmpOrigins := make([]string, 0, len(originSet))
		for origin := range originSet {
			tmpOrigins = append(tmpOrigins, origin)
		}
		// sort origins
		sort.Strings(tmpOrigins)
		// assign to CIMType
		t.Origins = append(t.Origins, tmpOrigins...)
	}
}

// reorderOrigins reorders the Origins field of each CIMType based on the priority of the ontologies.
// And also reorders the Origins field of each attribute based on the priority of the ontologies.
func (cimSpec *CIMSpecification) reorderOrigins() {
	for _, t := range cimSpec.Types {
		sort.Slice(t.Origins, func(i, j int) bool {
			originI := t.Origins[i]
			originJ := t.Origins[j]
			priorityI := cimSpec.Ontologies[originI].Priority
			priorityJ := cimSpec.Ontologies[originJ].Priority
			return priorityI < priorityJ
		})
		// reorder the Origins field of each attribute
		for _, attr := range t.Attributes {
			sort.Slice(attr.Origins, func(i, j int) bool {
				originI := attr.Origins[i]
				originJ := attr.Origins[j]
				priorityI := cimSpec.Ontologies[originI].Priority
				priorityJ := cimSpec.Ontologies[originJ].Priority
				return priorityI < priorityJ
			})
		}
	}
}

// setMainOrigin selects the main origin for each CIMType based on the Origins field of the attributes.
// The origin that appears most frequently in the Origins field of the attributes is selected as the main origin.
// If there is a tie, the first origin in the list is selected.
// Only the attributes are considered that have more than one entry in the Origins field.
// If "EQ" is among the most frequent origins, it is selected as the main origin.
// Otherwise, the first origin in alphabetical order is selected.
// This function updates the Origin field of each CIMType accordingly.
func (cimSpec *CIMSpecification) setMainOrigin() {
	for _, t := range cimSpec.Types {

		originCount := make(map[string]int)
		tmpType := t
		id := t.Id
		for id != "" {
			for _, attr := range tmpType.Attributes {
				if len(attr.Origins) > 1 {
					for _, origin := range attr.Origins {
						if contains(t.Origins, origin) {
							originCount[origin]++
						}

					}
				}
			}
			// Move to the super type to check its attributes
			if tmpType.SuperType != "" {
				if superType, ok := cimSpec.Types[tmpType.SuperType]; ok {
					tmpType = superType
					id = tmpType.Id
				} else {
					break
				}
			} else {
				break
			}
		}

		filteredOrigins := make([]string, 0, len(t.Origins))
		if len(originCount) > 0 {
			maxCount := 0
			for _, count := range originCount {
				if count > maxCount {
					maxCount = count
				}
			}

			for origin, count := range originCount {
				if count == maxCount {
					filteredOrigins = append(filteredOrigins, origin)
				}
			}
		} else {
			filteredOrigins = t.Origins
		}

		if contains(filteredOrigins, "EQ") {
			t.Origin = "EQ"
		} else {
			sort.Strings(filteredOrigins)
			t.Origin = filteredOrigins[0]
		}
	}
}

// contains checks if a string slice contains a specific string.
func contains(slice []string, str string) bool {
	for _, v := range slice {
		if v == str {
			return true
		}
	}
	return false
}

// sortAttributes sorts the attributes of each CIMType by their Id.
func (cimSpec *CIMSpecification) sortAttributes() {
	for _, t := range cimSpec.Types {
		sort.Slice(t.Attributes, func(i, j int) bool {
			return t.Attributes[i].Id < t.Attributes[j].Id
		})
	}
}

// setHasInverseRole iterates over all CIMTypes and attributes
// and sets the HasInverseRole flag if the InverseRole field is not empty.
// It also extracts the InverseRoleAttribute from the InverseRole field.
func (cimSpec *CIMSpecification) setHasInverseRole() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.CIMInverseRole != "" {
				attr.HasInverseRole = true
				parts := strings.Split(attr.CIMInverseRole, ".")
				if len(parts) == 2 {
					attr.InverseRoleAttribute = parts[1]
				}
			}
		}
	}
}

// setIsFixedAttributes sets the IsFixed flag for attributes based on the CIMIsFixed field.
func (cimSpec *CIMSpecification) setIsFixedAttributes() {
	for _, t := range cimSpec.CIMDatatypes {
		for _, attr := range t.Attributes {
			if attr.CIMIsFixed != "" {
				attr.IsFixed = true
			}
		}
	}
}

// fixMissingMRIDs adds missing MRID attributes to types that should have them.
func (cimSpec *CIMSpecification) fixMissingMRIDs() {
	for _, t := range cimSpec.Types {
		if (t.CIMStereotype == "concrete" || t.CIMStereotype == "") && t.SuperType == "" && t.Id != "IdentifiedObject" {
			t.Attributes = append(t.Attributes, &CIMAttribute{
				Id:            "MRID",
				Label:         "mRID",
				Comment:       "Master resource identifier issued by a model authority. The mRID is unique within an exchange context. Global uniqueness is easily achieved by using a UUID, as specified in RFC 4122, for the mRID. The use of UUID is strongly recommended. For CIMXML data files in RDF syntax conforming to IEC 61970-552, the mRID is mapped to rdf:ID or rdf:about attributes that identify CIM object elements.",
				CIMStereotype: "attribute",
				CIMDataType:   "String",
				IsPrimitive:   true,
				RDFType:       "Property",
			})
			//log.Println("Added missing MRID to type", t.Id)
		}
	}
}

// markUnusedAttributesAndAssociations marks attributes and associations as unused if they are not used.
// An attribute is marked as unused if it is an association (DataTypeObject) and its AssociationUsed flag is false.
// For list associations that are unused, the attribute is marked as unused.
// For non-list associations that are unused, the attribute is marked as primitive.
// This function updates the IsUsed and IsPrimitive fields of each CIMAttribute accordingly.
func (cimSpec *CIMSpecification) markUnusedAttributesAndAssociations() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			attr.IsUsed = true
			if !attr.IsAssociationUsed {
				if attr.CIMDataType == DataTypeObject {
					if attr.IsList {
						attr.IsUsed = false
						//log.Println("Marked unused list association", t.Id+"."+attr.Id, "of type", attr.Range)
					}
				} else {
					//attr.IsPrimitive = true
					//log.Println("Replaced association with primitive", t.Id+"."+attr.Id, "of type", attr.DataType)
				}
			}
		}
	}
}

// renameIdentifiedObjectAttributes renames attributes named "IdentifiedObject" to avoid conflicts.
func (cimSpec *CIMSpecification) renameIdentifiedObjectAttributes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.Label == "IdentifiedObject" {
				attr.Label = t.Label + "IdentifiedObject"
				//log.Println("Renamed IdentifiedObject attribute to", attr.Label, "in type", t.Id)
			}
		}
	}
}

// setMissingNamespaces fills in missing namespaces for types and their attributes and enums using the base URI.
// It also ensures that the "md" namespace is present in the CIMSpecification.
// It stores the namespaces that are used in the UsedNamespaces map.
func (cimSpec *CIMSpecification) setMissingNamespaces() {

	for _, t := range cimSpec.Types {
		if !strings.HasSuffix(t.Namespace, "#") {
			t.Namespace += "#"
		}

		if t.Namespace == "" || t.Namespace == "#" {
			t.Namespace = cimSpec.SpecificationNamespaces["base"]
		}
		for _, attr := range t.Attributes {
			if !strings.HasSuffix(attr.Namespace, "#") {
				attr.Namespace += "#"
			}
			if attr.Namespace == "" || attr.Namespace == "#" {
				attr.Namespace = cimSpec.SpecificationNamespaces["base"]
			}
		}
	}
	for _, e := range cimSpec.Enums {
		if !strings.HasSuffix(e.Namespace, "#") {
			e.Namespace += "#"
		}
		if e.Namespace == "" || e.Namespace == "#" {
			e.Namespace = cimSpec.SpecificationNamespaces["base"]
		}
	}

	revNamespaces := make(map[string]string)
	// store namespaces in map where value and key are reversed
	for key, value := range cimSpec.SpecificationNamespaces {
		if key != "base" {
			revNamespaces[value] = key
		}
	}

	// fill UsedNamespaces map
	for _, t := range cimSpec.Types {
		if _, ok := revNamespaces[t.Namespace]; ok {
			cimSpec.ProfileNamespaces[revNamespaces[t.Namespace]] = t.Namespace
		}
	}
	for _, e := range cimSpec.Enums {
		if _, ok := revNamespaces[e.Namespace]; ok {
			cimSpec.ProfileNamespaces[revNamespaces[e.Namespace]] = e.Namespace
		}
	}

	// add md namespace if not present
	if _, ok := cimSpec.ProfileNamespaces["md"]; !ok {
		cimSpec.SpecificationNamespaces["md"] = "http://iec.ch/TC57/61970-552/ModelDescription/1#"
		cimSpec.ProfileNamespaces["md"] = "http://iec.ch/TC57/61970-552/ModelDescription/1#"
	}

	// add rdf namespace if not present
	if _, ok := cimSpec.ProfileNamespaces["rdf"]; !ok {
		cimSpec.SpecificationNamespaces["rdf"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		cimSpec.ProfileNamespaces["rdf"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	}
}

func (cimSpec *CIMSpecification) setProfilePriorities() {
	if _, ok := cimSpec.Ontologies["EQ"]; ok {
		cimSpec.Ontologies["EQ"].Priority = 1
		cimSpec.OntologyList = append(cimSpec.OntologyList, cimSpec.Ontologies["EQ"])
	}

	// assign remaining ontologies priorities based on alphabetical order of their keywords
	keywords := make([]string, 0, len(cimSpec.Ontologies))
	for k := range cimSpec.Ontologies {
		if k != "EQ" {
			keywords = append(keywords, k)
		}
	}
	sort.Strings(keywords)
	priority := 2
	for _, k := range keywords {
		cimSpec.Ontologies[k].Priority = priority
		cimSpec.OntologyList = append(cimSpec.OntologyList, cimSpec.Ontologies[k])
		priority++
	}
}

// setLangTypesPython sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "list"
			} else {
				attr.LangType = MapDatatypePython(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypePython(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypePython(t.PrimitiveType)
	}
}

func MapDatatypePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "str"
	case DataTypeInteger:
		return "int"
	case DataTypeBoolean:
		return "bool"
	case DataTypeFloat:
		return "float"
	case DataTypeObject:
		return "Optional[str]"
	default:
		return "str"
	}
}

// setDefaultValuesPython sets default values for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "None" // Set default value for list attributes
			} else {
				attr.DefaultValue = MapDefaultValuePython(attr.DataType)
			}
		}
	}
}

func MapDefaultValuePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "''"
	case DataTypeInteger:
		return "0"
	case DataTypeBoolean:
		return "False"
	case DataTypeFloat:
		return "0.0"
	case DataTypeObject:
		return "None"
	default:
		return "None"
	}
}

// setLangTypesPython sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesJava() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "HashSet"
			} else {
				attr.LangType = MapDatatypeJava(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypeJava(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypeJava(t.PrimitiveType)
	}
}

func MapDatatypeJava(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "String"
	case DataTypeInteger:
		return "Integer"
	case DataTypeBoolean:
		return "Boolean"
	case DataTypeFloat:
		return "Double"
	case DataTypeObject:
		return "Class"
	default:
		return "String"
	}
}
