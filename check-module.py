"""Compare the candidate module with the captured LX2 kernel and stock module."""
import json
import os
from collections import defaultdict
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parent
STOCK = Path(os.environ["HMGAPI_TEST_STOCK"])
KERNEL = Path(os.environ["HMGAPI_TEST_KERNEL"])


def value(die, key, default=None):
    attribute = die.attributes.get(key)
    if attribute is None:
        return default
    result = attribute.value
    if isinstance(result, bytes):
        return result.decode(errors="replace")
    if isinstance(result, list):
        if key == "DW_AT_data_member_location" and result[0] == 0x23:
            offset = 0
            shift = 0
            for byte in result[1:]:
                offset |= (byte & 0x7f) << shift
                if byte < 0x80:
                    return offset
                shift += 7
            raise ValueError("Incomplete DW_OP_plus_uconst")
        return tuple(result)
    return result


def shape(die, depth=0):
    if die is None:
        return ("void",)
    if depth > 12:
        raise ValueError("Unexpected recursive anonymous type")
    if die.tag in {"DW_TAG_typedef", "DW_TAG_const_type", "DW_TAG_volatile_type", "DW_TAG_restrict_type"}:
        target = die.get_DIE_from_attribute("DW_AT_type") if "DW_AT_type" in die.attributes else None
        return shape(target, depth + 1)
    name = value(die, "DW_AT_name")
    size = value(die, "DW_AT_byte_size")
    if die.tag == "DW_TAG_pointer_type":
        return ("pointer", size or die.cu["address_size"])
    if die.tag == "DW_TAG_array_type":
        bounds = tuple(
            (value(child, "DW_AT_lower_bound", 0), value(child, "DW_AT_upper_bound"), value(child, "DW_AT_count"))
            for child in die.iter_children() if child.tag == "DW_TAG_subrange_type"
        )
        return ("array", bounds, shape(die.get_DIE_from_attribute("DW_AT_type"), depth + 1))
    if name:
        return (die.tag, name, size)
    if die.tag in {"DW_TAG_structure_type", "DW_TAG_union_type"}:
        return (die.tag, size, members(die, depth + 1))
    return (die.tag, size, value(die, "DW_AT_encoding"))


def members(die, depth=0):
    result = []
    for child in die.iter_children():
        if child.tag == "DW_TAG_member":
            target = child.get_DIE_from_attribute("DW_AT_type")
            result.append((
                value(child, "DW_AT_name"),
                value(child, "DW_AT_data_member_location", 0),
                value(child, "DW_AT_bit_size"),
                value(child, "DW_AT_bit_offset"),
                shape(target, depth),
            ))
        elif child.tag == "DW_TAG_enumerator":
            result.append((value(child, "DW_AT_name"), value(child, "DW_AT_const_value")))
    return tuple(result)


def layouts(path):
    result = defaultdict(set)
    with path.open("rb") as stream:
        dwarf = ELFFile(stream).get_dwarf_info()
        for cu in dwarf.iter_CUs():
            for die in cu.iter_DIEs():
                if die.tag not in {"DW_TAG_structure_type", "DW_TAG_union_type", "DW_TAG_enumeration_type"}:
                    continue
                name = value(die, "DW_AT_name")
                size = value(die, "DW_AT_byte_size")
                if name and size is not None and not value(die, "DW_AT_declaration", False):
                    result[(die.tag, name)].add((size, members(die)))
    return result


def module_info(path):
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        metadata = elf.get_section_by_name(".modinfo").data().decode().split("\0")
        symbols = elf.get_section_by_name(".symtab")
        undefined = {symbol.name for symbol in symbols.iter_symbols()
                     if symbol["st_shndx"] == "SHN_UNDEF" and symbol.name}
        return metadata, undefined


with KERNEL.open("rb") as stream:
    exports = {symbol.name.removeprefix("__ksymtab_")
               for symbol in ELFFile(stream).get_section_by_name(".symtab").iter_symbols()
               if symbol.name.startswith("__ksymtab_")}

candidate_info, required = module_info(ROOT / "driver-build/build/bcmdhd-rtl8822bu.ko")
stock_info, _ = module_info(STOCK)
stock_layouts = layouts(STOCK)
candidate_layouts = layouts(ROOT / "driver-build/build/bcmdhd-rtl8822bu.debug.ko")
common = stock_layouts.keys() & candidate_layouts.keys()
differences = []
for key in sorted(common):
    if stock_layouts[key].isdisjoint(candidate_layouts[key]):
        differences.append({"tag": key[0], "name": key[1],
                            "stock": sorted(stock_layouts[key], key=repr),
                            "candidate": sorted(candidate_layouts[key], key=repr)})

report = {
    "required_symbols": len(required),
    "missing_symbols": sorted(required - exports),
    "stock_vermagic": next(item for item in stock_info if item.startswith("vermagic=")),
    "candidate_vermagic": next(item for item in candidate_info if item.startswith("vermagic=")),
    "usb_2357_012e_alias": [item for item in candidate_info if item.startswith("alias=usb:v2357p012E")],
    "shared_named_types": len(common),
    "matching_shared_named_types": len(common) - len(differences),
    "different_shared_named_types": differences,
    "limits": ["Only named types represented in both modules' DWARF are compared.",
               "Pointer targets and function signatures require separate review.",
               "A successful static comparison does not establish runtime compatibility."],
}
(ROOT / "driver-build/build/compatibility.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: val for key, val in report.items() if key != "different_shared_named_types"}, indent=2))
print("Different types", [entry["name"] for entry in differences])
