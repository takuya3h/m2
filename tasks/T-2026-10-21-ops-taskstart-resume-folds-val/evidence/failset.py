import sys, xml.etree.ElementTree as ET
r = ET.parse(sys.argv[1]).getroot()
s = r if r.tag == "testsuite" else r.find("testsuite")
print("tests", s.get("tests"), "failures", s.get("failures"), "errors", s.get("errors"), "skipped", s.get("skipped"))
for tc in s.iter("testcase"):
    for k in ("failure", "error"):
        if tc.find(k) is not None:
            print(k.upper(), f"{tc.get('classname')}::{tc.get('name')}")
