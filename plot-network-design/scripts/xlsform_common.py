#!/usr/bin/env python3
"""Shared helpers for the TRPA Survey123 XLSForm builders.

Structure, column layout, and helper names follow build_xlsform.py (v1.0)
so that the three builders read the same way. Adds a pyxform validation
step and an openpyxl sanity check that the v1.0 builder did not have.
"""

import os
import sys
import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

SURVEY_COLS = [
    "type", "name", "label", "hint", "required", "readonly", "relevant",
    "constraint", "constraint_message", "calculation", "default", "appearance",
    "repeat_count", "choice_filter", "bind::esri:fieldType",
    "bind::esri:fieldLength", "bind::esri:parameters", "body::esri:style",
    "parameters",
]
CHOICES_COLS = ["list_name", "name", "label"]
SETTINGS_COLS = ["form_title", "form_id", "version", "instance_name",
                 "submission_url", "style", "default_language", "namespaces"]

TODAY = datetime.date.today().strftime("%Y%m%d")

# Esri field type shorthands
STR = "esriFieldTypeString"
INT = "esriFieldTypeInteger"
DBL = "esriFieldTypeDouble"
DATE = "esriFieldTypeDate"


class FormBuilder:
    """Collects survey rows, choice rows, and settings, then writes and validates."""

    def __init__(self, form_title, form_id, instance_name, version=None):
        self.S = []
        self.C = []
        self.form_title = form_title
        self.form_id = form_id
        self.instance_name = instance_name
        self.version = version or TODAY
        self._lists = set()

    # ---- row helpers (same names as build_xlsform.py) ---------------------
    def row(self, **kw):
        r = {c: "" for c in SURVEY_COLS}
        for k, v in kw.items():
            if k not in r:
                raise KeyError(f"unknown survey column {k}")
            r[k] = v
        self.S.append(r)

    def note(self, name, label, **kw):
        self.row(type="note", name=name, label=label, **kw)

    def grp(self, name, label, appearance="field-list", **kw):
        self.row(type="begin group", name=name, label=label,
                 appearance=appearance, **kw)

    def endgrp(self):
        self.row(type="end group", name="", label="")

    def rep(self, name, label, repeat_count="", **kw):
        self.row(type="begin repeat", name=name, label=label,
                 repeat_count=repeat_count, **kw)

    def endrep(self):
        self.row(type="end repeat", name="", label="")

    def choices(self, list_name, pairs):
        self._lists.add(list_name)
        for n, l in pairs:
            self.C.append((list_name, n, l))

    # ---- typed field shorthands --------------------------------------------
    def text(self, name, label, length=100, **kw):
        kw.setdefault("bind::esri:fieldType", STR)
        kw.setdefault("bind::esri:fieldLength", str(length))
        self.row(type="text", name=name, label=label, **kw)

    def integer(self, name, label, **kw):
        kw.setdefault("bind::esri:fieldType", INT)
        self.row(type="integer", name=name, label=label, **kw)

    def decimal(self, name, label, **kw):
        kw.setdefault("bind::esri:fieldType", DBL)
        self.row(type="decimal", name=name, label=label, **kw)

    def date(self, name, label, **kw):
        kw.setdefault("bind::esri:fieldType", DATE)
        self.row(type="date", name=name, label=label, **kw)

    def datetime(self, name, label, **kw):
        kw.setdefault("bind::esri:fieldType", DATE)
        self.row(type="dateTime", name=name, label=label, **kw)

    def select1(self, list_name, name, label, length=20, **kw):
        kw.setdefault("bind::esri:fieldType", STR)
        kw.setdefault("bind::esri:fieldLength", str(length))
        self.row(type=f"select_one {list_name}", name=name, label=label, **kw)

    def selectm(self, list_name, name, label, length=200, **kw):
        kw.setdefault("bind::esri:fieldType", STR)
        kw.setdefault("bind::esri:fieldLength", str(length))
        self.row(type=f"select_multiple {list_name}", name=name, label=label,
                 **kw)

    def species(self, name, label, woody_only=True, required="yes", length=10,
                **kw):
        """Species from species_list.csv in the media folder, TEON style."""
        kw.setdefault("bind::esri:fieldType", STR)
        kw.setdefault("bind::esri:fieldLength", str(length))
        kw.setdefault("appearance", "autocomplete")
        if woody_only:
            kw.setdefault("choice_filter", "woody=1")
        self.row(type="select_one_from_file species_list.csv", name=name,
                 label=label, required=required, **kw)

    def unk_species(self, species_field, name, label="Unknown code or notes"):
        """TEON convention: a free text field opens when an UNK code is chosen."""
        self.text(name, label, length=60,
                  relevant=f"contains(${{{species_field}}}, 'UNK')",
                  hint="Describe the unknown, or give the office-assigned UNK number")

    def calc(self, name, calculation, ftype=DBL, **kw):
        kw.setdefault("bind::esri:fieldType", ftype)
        self.row(type="calculate", name=name, calculation=calculation, **kw)

    def yesno(self, name, label, **kw):
        self.select1("yesno", name, label, length=5, **kw)

    def image(self, name, label, **kw):
        kw.setdefault("parameters", "max-pixels=2048")
        self.row(type="image", name=name, label=label, **kw)

    def geopoint(self, name, label, **kw):
        self.row(type="geopoint", name=name, label=label, **kw)

    # ---- output --------------------------------------------------------------
    def write(self, out_path):
        wb = Workbook()
        hdr_font = Font(bold=True, color="FFFFFF")
        hdr_fill = PatternFill("solid", fgColor="1F4E79")

        ws = wb.active
        ws.title = "survey"
        ws.append(SURVEY_COLS)
        for r in self.S:
            ws.append([r[c] for c in SURVEY_COLS])

        ws2 = wb.create_sheet("choices")
        ws2.append(CHOICES_COLS)
        for t in self.C:
            ws2.append(list(t))

        ws3 = wb.create_sheet("settings")
        ws3.append(SETTINGS_COLS)
        ws3.append([self.form_title, self.form_id, self.version,
                    self.instance_name, "", "pages", "English (en)",
                    'esri="https://esri.com/xforms"'])

        for sheet in (ws, ws2, ws3):
            for cell in sheet[1]:
                cell.font = hdr_font
                cell.fill = hdr_fill
                cell.alignment = Alignment(vertical="center")
            sheet.freeze_panes = "A2"

        widths = {"survey": [24, 26, 62, 56, 9, 9, 40, 44, 46, 40, 12, 20,
                             12, 18, 26, 14, 26, 16, 20],
                  "choices": [20, 18, 62],
                  "settings": [30, 30, 12, 62, 16, 10, 14, 30]}
        for name, ws_w in widths.items():
            sh = wb[name]
            for i, w in enumerate(ws_w, start=1):
                sh.column_dimensions[get_column_letter(i)].width = w

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        wb.save(out_path)
        return out_path

    def check_names(self):
        """Fail early on duplicate field names, which Survey123 rejects."""
        seen = {}
        for r in self.S:
            n = r["name"]
            if not n or r["type"] in ("end group", "end repeat"):
                continue
            if n in seen:
                raise ValueError(f"duplicate field name: {n}")
            seen[n] = r["type"]
        # every select list referenced must exist
        for r in self.S:
            t = r["type"]
            if t.startswith("select_one ") or t.startswith("select_multiple "):
                ln = t.split(" ", 1)[1]
                if ln.endswith(".csv"):
                    continue
                if ln not in self._lists:
                    raise ValueError(f"missing choice list: {ln} for {r['name']}")


def validate(xlsx_path, xml_path=None):
    """Run pyxform, then ODK Validate if Java is present. Returns warnings."""
    from pyxform.xls2xform import xls2xform_convert
    xml_path = xml_path or os.path.splitext(xlsx_path)[0] + ".xml"
    try:
        warnings = xls2xform_convert(xlsx_path, xml_path, validate=True,
                                     pretty_print=False)
    except Exception as e:  # noqa: BLE001
        print(f"pyxform FAILED for {os.path.basename(xlsx_path)}: {e}")
        raise
    # ODK Validate echoes the JVM's JAVA_TOOL_OPTIONS banner as a "warning";
    # it is environment noise, not a form warning, so drop it.
    real = []
    for w in warnings:
        lines = [ln for ln in w.splitlines()
                 if ln.strip() and not ln.startswith("Picked up JAVA_TOOL_OPTIONS")
                 and ln.strip() != "ODK Validate Warnings:"]
        if lines:
            real.append("\n".join(lines))
    print(f"pyxform OK: {os.path.basename(xlsx_path)}  "
          f"({len(real)} warnings, ODK Validate passed)")
    for w in real:
        print("   warning:", w.strip().replace("\n", " ")[:300])
    return real


def sanity(xlsx_path):
    """Open with openpyxl and report survey row count, field count, repeats."""
    wb = load_workbook(xlsx_path)
    ws = wb["survey"]
    hdr = [c.value for c in ws[1]]
    ti, ni = hdr.index("type"), hdr.index("name")
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    repeats = [r[ni] for r in rows if r[ti] == "begin repeat"]
    groups = [r[ni] for r in rows if r[ti] == "begin group"]
    skip = {"begin group", "end group", "begin repeat", "end repeat", "note",
            None, ""}
    fields = [r for r in rows if r[ti] not in skip]
    calcs = [r for r in fields if r[ti] == "calculate"]
    print(f"{os.path.basename(xlsx_path)}: survey rows={len(rows)}, "
          f"fields={len(fields)} (of which calculate={len(calcs)}), "
          f"groups={len(groups)}, repeats={len(repeats)}")
    print("   repeats:", ", ".join(repeats))
    print("   choices rows:", wb["choices"].max_row - 1)
    return {"rows": len(rows), "fields": len(fields), "repeats": repeats}


def finish(fb, out_path):
    fb.check_names()
    fb.write(out_path)
    print("saved:", out_path, "survey rows:", len(fb.S), "choice rows:",
          len(fb.C))
    validate(out_path)
    return sanity(out_path)
