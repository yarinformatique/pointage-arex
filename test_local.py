import urllib.request
import traceback

res = ""
try:
    with urllib.request.urlopen("http://127.0.0.1:8080/scanner", timeout=3) as resp:
        res = f"STATUS: {resp.status}, LENGTH: {len(resp.read())}"
except Exception as e:
    res = f"ERROR: {e}\n{traceback.format_exc()}"

with open(r"C:\Users\USER\Desktop\pointage_arex\test_local_result.txt", "w", encoding="utf-8") as f:
    f.write(res)
