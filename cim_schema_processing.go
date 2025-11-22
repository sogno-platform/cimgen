package cimgen

import (
	"fmt"
	"sort"
)

// postprocess performs various post-processing steps on the CIMSpecification.
func (cimSpec *CIMSpecification) postprocess() {
	cimSpec.pickMainOrigin()
	cimSpec.sortAttributes()
	cimSpec.determineDataTypes()
	cimSpec.setDefaultValuesPython()
	cimSpec.setLangTypesPython()
	cimSpec.fixMissingMRIDs()
	cimSpec.markUnusedAttributesAndAssociations()
	cimSpec.removeIdentifiedObjectAttributes()
	cimSpec.fillMissingNamespaces()
	cimSpec.setProfilePriorities()
}

// pickMainOrigin selects the main origin for each CIMType based on the Origins field of the attributes.
// The origin that appears most frequently in the Origins field of the attributes is selected as the main origin.
// If there is a tie, the first origin in the list is selected.
// Only the attributes are considered that have more than one entry in the Origins field.
// If "EQ" is among the most frequent origins, it is selected as the main origin.
// Otherwise, the first origin in alphabetical order is selected.
// This function updates the Origin field of each CIMType accordingly.
func (cimSpec *CIMSpecification) pickMainOrigin() {
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
		//fmt.Println("Origin count map:", originCount, "for type", t.Id)

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

// determineDataTypes determines the data types of attributes and marks them as primitive if applicable.
func (cimSpec *CIMSpecification) determineDataTypes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if IsPrimitiveType(attr.DataType) {
				attr.IsPrimitive = true
			} else if IsEnumType(attr.DataType, cimSpec) {
				attr.IsEnumValue = true
			} else if IsCIMDatatype(attr.DataType) {
				attr.IsCIMDatatype = true
			} else if attr.DataType == DataTypeObject || attr.DataType == "" {
				attr.IsClass = true
			}
		}
	}
}

// isDataType checks if the given type string is a known data type.
func IsPrimitiveType(typeStr string) bool {
	switch typeStr {
	case DataTypeString, DataTypeInteger, DataTypeBoolean,
		DataTypeFloat, DataTypeDate, DataTypeTime,
		DataTypeDateTime, DataTypeBinary:
		return true
	default:
		return false
	}
}

// is CIMDatatype checks if the given type string is a known CIM data type.
func IsCIMDatatype(typeStr string) bool {
	switch typeStr {
	case DataTypeActivePower, DataTypeActivePowerPerCurrentFlow, DataTypeActivePowerPerFrequency,
		DataTypeAngleDegrees, DataTypeAngleRadians, DataTypeApparentPower,
		DataTypeArea, DataTypeCapacitance, DataTypeConductance, DataTypeCurrentFlow,
		DataTypeFrequency, DataTypeInductance, DataTypeLength, DataTypeMoney,
		DataTypePerCent, DataTypePU, DataTypeReactance, DataTypeReactivePower,
		DataTypeRealEnergy, DataTypeResistance, DataTypeRotationSpeed, DataTypeSeconds,
		DataTypeSusceptance, DataTypeTemperature, DataTypeVoltage, DataTypeVoltagePerReactivePower,
		DataTypeVolumeFlowRate:
		return true
	default:
		return false
	}
}

// isEnumType checks if the given type string is a known enumeration type.
func IsEnumType(typeStr string, cimSpec *CIMSpecification) bool {
	if _, ok := cimSpec.Enums[typeStr]; ok {
		return true
	}
	return false
}

// fixMissingMRIDs adds missing MRID attributes to types that should have them.
func (cimSpec *CIMSpecification) fixMissingMRIDs() {
	for _, t := range cimSpec.Types {
		if (t.Stereotype == "concrete" || t.Stereotype == "") && t.SuperType == "" && t.Id != "IdentifiedObject" {
			t.Attributes = append(t.Attributes, &CIMAttribute{
				Id:              "MRID",
				Label:           "mRID",
				Namespace:       "",
				Comment:         "Master resource identifier issued by a model authority. The mRID is unique within an exchange context. Global uniqueness is easily achieved by using a UUID, as specified in RFC 4122, for the mRID. The use of UUID is strongly recommended. For CIMXML data files in RDF syntax conforming to IEC 61970-552, the mRID is mapped to rdf:ID or rdf:about attributes that identify CIM object elements.",
				IsList:          false,
				AssociationUsed: false,
				IsFixed:         false,
				InverseRole:     "",
				Stereotype:      "attribute",
				Range:           "",
				DataType:        "String",
				IsPrimitive:     true,
				RDFDomain:       "",
				RDFType:         "Property",
				DefaultValue:    "''",
			})
			fmt.Println("Added missing MRID to type", t.Id)
		}
	}
}

// markUnusedAttributesAndAssociations marks attributes and associations as unused if they are not used.
func (cimSpec *CIMSpecification) markUnusedAttributesAndAssociations() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			attr.IsUsed = true
			if !attr.AssociationUsed {
				if attr.DataType == DataTypeObject {
					if attr.IsList {
						attr.IsUsed = false
						fmt.Println("Marked unused list association", t.Id+"."+attr.Id, "of type", attr.Range)
					}
				} else {
					attr.IsPrimitive = true
					fmt.Println("Replaced association with primitive", t.Id+"."+attr.Id, "of type", attr.DataType)
				}
			}
		}
	}
}

// removeIdentifiedObjectAttributes renames attributes named "IdentifiedObject" to avoid conflicts.
func (cimSpec *CIMSpecification) removeIdentifiedObjectAttributes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.Label == "IdentifiedObject" {
				attr.Label = t.Label + "IdentifiedObject"
				fmt.Println("Renamed IdentifiedObject attribute to", attr.Label, "in type", t.Id)
			}
		}
	}
}

// fillMissingNamespaces fills in missing namespaces for types and their attributes and enums using the base URI.
// It also ensures that the "md" namespace is present in the CIMSpecification.
// It stores the namespaces that are used in the UsedNamespaces map.
func (cimSpec *CIMSpecification) fillMissingNamespaces() {
	for _, t := range cimSpec.Types {
		if t.Namespace == "" || t.Namespace == "#" {
			t.Namespace = cimSpec.SpecificationNamespaces["base"]
		}
		for _, attr := range t.Attributes {
			if attr.Namespace == "" || t.Namespace == "#" {
				attr.Namespace = cimSpec.SpecificationNamespaces["base"]
			}
		}
	}
	for _, e := range cimSpec.Enums {
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
	cimSpec.Ontologies["EQ"].Priority = 1

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
		priority++
	}
}

// setLangTypesPython sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "list" // Set default value for list attributes
			} else if attr.DataType == DataTypeString {
				attr.LangType = "str" // Set default value for string attributes
			} else if attr.DataType == DataTypeInteger {
				attr.LangType = "int" // Set default value for integer attributes
			} else if attr.DataType == DataTypeBoolean {
				attr.LangType = "bool" // Set default value for boolean attributes
			} else if attr.DataType == DataTypeFloat {
				attr.LangType = "float" // Set default value for float attributes
			} else if attr.DataType == DataTypeObject {
				attr.LangType = "Optional[str]" // Set default value for object attributes
			} else if attr.DataType == DataTypeActivePower || attr.DataType == DataTypeActivePowerPerCurrentFlow ||
				attr.DataType == DataTypeActivePowerPerFrequency || attr.DataType == DataTypeAngleDegrees ||
				attr.DataType == DataTypeAngleRadians || attr.DataType == DataTypeApparentPower ||
				attr.DataType == DataTypeArea || attr.DataType == DataTypeCapacitance || attr.DataType == DataTypeConductance ||
				attr.DataType == DataTypeCurrentFlow || attr.DataType == DataTypeFrequency ||
				attr.DataType == DataTypeInductance || attr.DataType == DataTypeLength || attr.DataType == DataTypeMoney ||
				attr.DataType == DataTypePerCent || attr.DataType == DataTypePU || attr.DataType == DataTypeReactance ||
				attr.DataType == DataTypeReactivePower || attr.DataType == DataTypeRealEnergy || attr.DataType == DataTypeResistance ||
				attr.DataType == DataTypeRotationSpeed || attr.DataType == DataTypeSeconds || attr.DataType == DataTypeSusceptance ||
				attr.DataType == DataTypeTemperature || attr.DataType == DataTypeVoltage || attr.DataType == DataTypeVoltagePerReactivePower ||
				attr.DataType == DataTypeVolumeFlowRate {
				attr.LangType = "float" // Set default value for specific CIM data types
			} else if attr.DataType == DataTypeDateTime {
				attr.LangType = "str" // Could be datetime, but keeping it simple for now
			} else {
				attr.LangType = "float" // Default fallback
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		switch t.Id {
		case DataTypeString:
			t.LangType = "str"
		case DataTypeInteger:
			t.LangType = "int"
		case DataTypeBoolean:
			t.LangType = "bool"
		case DataTypeFloat:
			t.LangType = "float"
		case DataTypeDate, DataTypeTime, DataTypeDateTime:
			t.LangType = "str" // Could be datetime, but keeping it simple for now
		case DataTypeBinary:
			t.LangType = "bytes"
		default:
			t.LangType = "str" // Default fallback
		}
	}

	for _, t := range cimSpec.CIMDatatypes {
		switch t.Id {
		case DataTypeActivePower, DataTypeActivePowerPerCurrentFlow, DataTypeActivePowerPerFrequency, DataTypeAngleDegrees, DataTypeAngleRadians, DataTypeApparentPower, DataTypeArea, DataTypeCapacitance, DataTypeConductance, DataTypeCurrentFlow, DataTypeFrequency, DataTypeInductance, DataTypeLength, DataTypeMoney, DataTypePerCent, DataTypePU, DataTypeReactance, DataTypeReactivePower, DataTypeRealEnergy, DataTypeResistance, DataTypeRotationSpeed, DataTypeSeconds, DataTypeSusceptance, DataTypeTemperature, DataTypeVoltage, DataTypeVoltagePerReactivePower, DataTypeVolumeFlowRate:
			t.LangType = "float" // Set default value for specific CIM data types
		case DataTypeDateTime:
			t.LangType = "str" // Could be datetime, but keeping it simple for now
		default:
			t.LangType = "str" // Default fallback
		}
	}
}

// setDefaultValuesPython sets default values for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "list" // Set default value for list attributes
			} else if attr.DataType == DataTypeString {
				attr.DefaultValue = "''" // Set default value for string attributes
			} else if attr.DataType == DataTypeInteger {
				attr.DefaultValue = "0" // Set default value for integer attributes
			} else if attr.DataType == DataTypeBoolean {
				attr.DefaultValue = "False" // Set default value for boolean attributes
			} else if attr.DataType == DataTypeFloat {
				attr.DefaultValue = "0.0" // Set default value for float attributes
			} else if attr.DataType == DataTypeObject {
				attr.DefaultValue = "None" // Set default value for object attributes
			} else if attr.DataType == DataTypeActivePower || attr.DataType == DataTypeActivePowerPerCurrentFlow ||
				attr.DataType == DataTypeActivePowerPerFrequency || attr.DataType == DataTypeAngleDegrees ||
				attr.DataType == DataTypeAngleRadians || attr.DataType == DataTypeApparentPower ||
				attr.DataType == DataTypeArea || attr.DataType == DataTypeCapacitance || attr.DataType == DataTypeConductance ||
				attr.DataType == DataTypeCurrentFlow || attr.DataType == DataTypeFrequency ||
				attr.DataType == DataTypeInductance || attr.DataType == DataTypeLength || attr.DataType == DataTypeMoney ||
				attr.DataType == DataTypePerCent || attr.DataType == DataTypePU || attr.DataType == DataTypeReactance ||
				attr.DataType == DataTypeReactivePower || attr.DataType == DataTypeRealEnergy || attr.DataType == DataTypeResistance ||
				attr.DataType == DataTypeRotationSpeed || attr.DataType == DataTypeSeconds || attr.DataType == DataTypeSusceptance ||
				attr.DataType == DataTypeTemperature || attr.DataType == DataTypeVoltage || attr.DataType == DataTypeVoltagePerReactivePower ||
				attr.DataType == DataTypeVolumeFlowRate {
				attr.DefaultValue = "0.0" // Set default value for specific CIM data types
			} else {
				attr.DefaultValue = "None" // Default fallback
			}
		}
	}
}
