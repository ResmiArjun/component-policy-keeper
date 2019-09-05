import kubernetes.client
import kubernetes.config
import logging
import pk_config
import time

dryrun_id='k8s'

def query_list_of_nodes(endpoint,worker_name='micado-worker',status='ready'):
  log=logging.getLogger('pk_k8s')
  list_of_nodes=[]
  if pk_config.dryrun_get(dryrun_id):
    log.info('(I)   DRYRUN enabled. Skipping...')
    a = {}
    a['ID']='dummyID'
    a['Addr']='127.0.0.1'
    list_of_nodes.append(a.copy())
    return list_of_nodes
  kubernetes.config.load_kube_config()
  client = kubernetes.client.CoreV1Api()
  try:
    if status=='ready':
      nodes = [x for x in client.list_node().items if not x.spec.taints]
      nodes = [x for x in nodes if x.metadata.labels.get('micado.eu/node_type') == worker_name]
    elif status=='down':
      nodes = [x for x in client.list_node().items if x.spec.taints and 'master' not in x.spec.taints[0].key]
    for n in nodes:
      a = {}
      a['ID']=n.metadata.name
      a['Addr']=n.status.addresses[0].address
      list_of_nodes.append(a.copy())
    return list_of_nodes
  except Exception as e:
    log.exception('(Q) Query of k8s nodes failed.')
    return dict()

def scale_k8s_deploy(endpoint,service_name,replicas):
  service_name = '-'.join(service_name.split('_')[1:])
  log=logging.getLogger('pk_k8s')
  log.info('(S)   => m_container_count: {0}'.format(replicas))
  if pk_config.dryrun_get(dryrun_id):
    log.info('(S)   DRYRUN enabled. Skipping...')
    return
  kubernetes.config.load_kube_config()
  client = kubernetes.client.ExtensionsV1beta1Api()
  try:
    dep = client.read_namespaced_deployment(service_name, "default")
    dep.spec.replicas = replicas
    client.patch_namespaced_deployment_scale(service_name, "default", dep)
  except Exception as e:
    log.warning('(S) Scaling of k8s service "{0}" failed: {1}'.format(service_name,str(e)))
  return

def query_k8s_replicas(endpoint,service_name):
  service_name = '-'.join(service_name.split('_')[1:])
  log=logging.getLogger('pk_k8s')
  instance = 1
  if pk_config.dryrun_get(dryrun_id):
    log.info('(I)   DRYRUN enabled. Skipping...')
    return instance
  kubernetes.config.load_kube_config()
  client = kubernetes.client.ExtensionsV1beta1Api()
  try:
    dep = client.read_namespaced_deployment(service_name, "default")
    replicas = dep.spec.replicas
    log.debug('(I)   => m_container_count for {0}: {1}'.format(service_name,replicas))
  except Exception as e:
    log.warning('(Q) Querying k8s service "{0}" replicas failed: {1}'.format(service_name,str(e)))
  return instance

down_nodes_stored={}

def remove_node(endpoint,id):
  log=logging.getLogger('pk_k8s')
  if pk_config.dryrun_get(dryrun_id):
    log.info('(M)   DRYRUN enabled. Skipping...')
    return
  kubernetes.config.load_kube_config()
  client = kubernetes.client.CoreV1Api()
  try:
    client.delete_node(id)
  except Exception:
    log.error('(M)   => Removing k8s node failed.')
  return

def down_nodes_cleanup_by_list(stored, actual):
  setStored = { v['ID'] for k,v in stored.items() }
  setActual = { x['ID'] for x in actual }
  missing = { x for x in setStored if x not in setActual }
  for x in missing:
    del stored[x]

def down_nodes_add_from_list(stored, actual):
  for node in actual:
    if 'ID' in node and node['ID'] not in stored:
      stored[node['ID']]=node
      stored[node['ID']]['micado_timestamp']=int(time.time())

def down_nodes_cleanup_by_timeout(endpoint, stored, timeout):
  log=logging.getLogger('pk_k8s')
  current_time = int(time.time())
  for id, node in stored.items():
    if node['micado_timestamp']+timeout < current_time:
      log.info('(M)   => Node {0} is down for more than {1} seconds, removing.'.format(id,timeout))
      remove_node(endpoint,id)
      del stored[id]

def down_nodes_maintenance(endpoint, down_nodes_timeout = 120):
  log=logging.getLogger('pk_k8s')
  if pk_config.dryrun_get(dryrun_id):
    log.info('(M)   DRYRUN enabled. Skipping...')
    return
  down_nodes_actual = query_list_of_nodes(endpoint,status='down')
  down_nodes_cleanup_by_list(down_nodes_stored, down_nodes_actual)
  down_nodes_add_from_list(down_nodes_stored, down_nodes_actual)
  down_nodes_cleanup_by_timeout(endpoint, down_nodes_stored, down_nodes_timeout)
  return
