"""Read-only release checks; never print secret values or inspect .env."""
import ast,base64,hashlib,io,json,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT)
def old_values():
    values=set()
    for path in ["backend/app/core/config.py","render.yaml"]:
        content=git("show","origin/main:"+path).decode("utf-8")
        if path.endswith(".py"):
            tree=ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node,(ast.Assign,ast.AnnAssign)):
                    names=[n.id for n in getattr(node,"targets",[]) if isinstance(n,ast.Name)]
                    if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):names.append(node.target.id)
                    if any(any(k in n for k in ("PASS","SECRET","ENCRYPTION_KEY")) for n in names):
                        value=node.value
                        if isinstance(value,ast.Constant) and isinstance(value.value,str) and len(value.value)>=16:values.add(value.value.encode())
                        for call in ast.walk(value):
                            if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr=="b64decode" and call.args and isinstance(call.args[0],ast.Constant):
                                raw=call.args[0].value
                                if isinstance(raw,(str,bytes)):
                                    values.add(base64.b64decode(raw))
        else:
            import yaml
            for svc in yaml.safe_load(content).get("services",[]):
                for env in svc.get("envVars",[]):
                    if any(k in env.get("key","") for k in ("PASSWORD","SECRET","ENCRYPTION_KEY","API_KEY")):
                        value=env.get("value")
                        if isinstance(value,str) and len(value)>=16:values.add(value.encode())
    return values
names=set(git("diff","--name-only","origin/main").decode().splitlines())
names.update(git("ls-files","--others","--exclude-standard").decode().splitlines())
bad_paths=[];leaks=[]
secrets=old_values()
for name in sorted(names):
    path=ROOT/name
    if not path.is_file():continue
    if any(p.startswith(".venv") or p in {"node_modules","__pycache__"} for p in path.relative_to(ROOT).parts) or path.name.startswith(".env") or path.suffix.lower() in {".onnx",".db",".sqlite",".sqlite3",".log",".tmp",".pem",".key"}:
        bad_paths.append(name);continue
    data=path.read_bytes()
    payloads=[data]
    if path.suffix in {".docx",".xlsx"}:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:payloads.extend(archive.read(p) for p in archive.namelist() if p.endswith(".xml"))
    if any(secret in payload for secret in secrets for payload in payloads):leaks.append(name)
unchanged=["red_neuronal","backend/app/services/parte6_service.py","backend/app/services/prediction_service.py","segmentacion/segmentacion_kmeans.py","segmentacion/experimental_expresiones/segmentacion_expresiones.py"]
changed_algorithms=git("diff","--name-only","origin/main","--",*unchanged).decode().splitlines()
result={"candidate_files":len(names),"forbidden_paths":bad_paths,"secret_copies":leaks,"inherited_secret_values_checked":len(secrets),"algorithm_or_weight_changes":changed_algorithms,
        "stash_hashes":git("stash","list","--format=%H").decode().splitlines(),
        "origin_main":git("rev-parse","origin/main").decode().strip(),"local_main":git("rev-parse","main").decode().strip()}
print(json.dumps(result,indent=2))
if bad_paths or leaks or changed_algorithms:raise SystemExit(1)
