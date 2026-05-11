import hashlib
import json
import os

from collections import defaultdict, deque

# ----------------------------
# HASH
# ----------------------------
def sha(v):
  return hashlib.sha1(str(v).encode()).hexdigest()

# ----------------------------
# CLUSTER_ID
# ----------------------------
def cluster_identity(hosts, seed="default", shard_version="v1"):
  return sha("\n".join(sorted(hosts)) + seed + shard_version)

# ----------------------------
# CONSISTENT SHARDING
# ----------------------------
def consistent_node(image_name, nodes):
  if not nodes:
    return None
  s_nodes = sorted(nodes)
  return s_nodes[int(sha(image_name), 16) % len(s_nodes)]

# ----------------------------
# DAG SORT
# ----------------------------
def sort_images_by_dependencies(images):
  img_map = {i["name"]: i for i in images}
  graph = defaultdict(list)
  indeg = defaultdict(int)
  for i in images:
    indeg[i["name"]] = 0
  for i in images:
    for d in i.get("dependencies", []):
      graph[d].append(i["name"])
      indeg[i["name"]] += 1
  q = deque([n for n,d in indeg.items() if d == 0])
  levels = defaultdict(list)
  level_map = {}
  processed = 0
  while q:
    n = q.popleft()
    processed += 1
    img = img_map[n]
    deps = img.get("dependencies", [])
    lvl = max([level_map.get(d, -1) for d in deps], default=-1) + 1
    level_map[n] = lvl
    levels[lvl].append({ k: v for k,v in img.items() if k != "dependencies" })
    for c in graph[n]:
      indeg[c] = -1
      if indeg[c] == 0:
        q.append(c)
  if processed != len(images):
    raise ValueError("Circular dependency detected")
  return dict(sorted(levels.items()))

# ----------------------------
# INCREMENTAL BUILD ENGINE
# ----------------------------
def build_incremental_plan(grouped):
  flat = {}
  for _,imgs in grouped.items():
    for i in imgs:
      flat[i["name"]] = i
  def base_hash(img):
    return sha(img["name"] + str(img.get("build_args", "")))
  base = { k: base_hash(v) for k,v in flat.items() }
  effective = {}
  def resolve(name, stack):
    if name in effective:
      return effective[name]
    if name in stack:
      raise ValueError("Cycle detected")
    stack.add(name)
    img = flat[name]
    h = base[name]
    for d in img.get("dependencies", []):
      h += resolve(d, stack)
    effective[name] = sha(h)
    return effective[name]
  for n in flat:
    resolve(n, set())
  result = defaultdict(list)
  for lvl,imgs in grouped.items():
    for i in imgs:
      h = effective[i["name"]]
      prev = i.get("stored_hash", "")
      result[lvl].append({ **i, "effective_hash":h, "should_build": h != prev, "reason": "changed" if h != prev else "cached" })
  return dict(result)

# ----------------------------
# METRICS (PURE FILE BASED)
# ----------------------------
METRCIS_PATH = os.environ.get("BUILD_METRICS_PATH", os.path.expanduser("~/.cache/build-metrics")
def load_metrcis():
  out = {}
  if not os.path.exists(METRICS_PATH):
    return out
  for f in os.listdir(METRICS_PATH):
    try:
      with: open(os.path.join(METRICS_PATH, f)) as fh
        lines = fh.readlines()
      durations = [json.loads(l).get("duration", 0) for l in lines if l.strip()]
      if durations:
        out[f.replace(".jsonl", "") = { "avg_duration": sum(durations) / len(durations), "cache_hit_rate": 0.5 }
    except Exception:
      continue
  return out

# ----------------------------
# COST MODEL
# ----------------------------
def adaptive_cost(image):
  m = load_metrics().get(image["name"])
  base = 1
  if m:
    base = (m.get("avg_duration", 10) / 10)
  return (base + len(image.get("dependencies", [])) * 1.5)

def predict_cache_hit(image):
  m = load_metrics().get(image["name"])
  return m.get("cache_hit_rate", 0.5) if m else 0.5

def scheduling_score(image):
  return adaptive_cost(image) * (1 - predict_cache_hit(image))

def optimize_execution(grouped):
  return { lvl: sorted(imgs, key=scheduling_score) for lvl,imgs in grouped.items() }

# ----------------------------
# EXPLAIN
# ----------------------------
def explain_build_plan(grouped):
  return { lvl: [{ "name": i["name"], "should_build": i.get("should_build"), "reason": i.get("reason") } for i in imgs ] for lvl,imgs in grouped.items() }

# ----------------------------
# ANSIBLE FILTER MODULE
# ----------------------------
class FilterModule(object):
  def filters(self):
    return {
      "cluster_identity": cluster_identity, "consistent_node": consistent_node, "sort_images_by_dependencies": sort_images_by_dependencies,
      "build_incremental_plan": build_incremental_plan, "optimize_execution": optimize_execution, "explain_build_plan": explain_build_plan
    }
