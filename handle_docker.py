import docker
import logging


def scale_docker_service(endpoint,service_name,replicas):
    log=logging.getLogger('pk_docker')
    log.info('Scaling docker service "{0}" to {1} replicas.'.format(service_name,replicas))
    client = docker.APIClient(endpoint)
    try: 
	version = client.inspect_service(service_name)['Version']['Index']
	ret = client.update_service(
            service_name,
            version,
            mode={'Replicated': {'Replicas': replicas}},
            fetch_current_spec=True)
    except Exception as e:
        log.exception('Scaling of docker service "{0}" failed:'.format(service_name))
    return

def query_service_network(endpoint, stack_name, service_name):
    id = None
    log=logging.getLogger('pk_docker')
    client = docker.DockerClient(base_url=endpoint)
    full_service_name = stack_name + "_" + service_name
    service_list = client.services.list()
    i = 0
    while i < len(service_list) and service_list[i].name != full_service_name:
        i += 1
    if i < len(service_list) and service_list[i].name == full_service_name:
        if len(service_list[i].attrs.get("Spec").get("TaskTemplate").get("Networks")) == 1:
            id = service_list[i].attrs.get("Spec").get("TaskTemplate").get("Networks")[0].get("Target")
            log.debug('Docker service "{0}" in stack "{1}" is connected to network "{2}" with id "{3}".'
			.format(service_name, stack_name, client.networks.get(id).name),str(id))
        else:
            log.warning('Docker service "{0}" is connected to more than one network.'.format(full_service_name))
    else:
        log.warning('Docker service "{0}" is not found in stack "{1}".'.format(service_name,stack_name))
    return id


def attach_container_to_network(endpoint, container, network_id):
    log=logging.getLogger('pk_docker')
    client = docker.DockerClient(base_url=endpoint)
    network = client.networks.get(network_id)
    if client.containers.get(container).status == "running":
        network.connect(container)
        log.info('Container "{0}" is connected to network "{1}".'.format(container, network.name))
    else:
        log.info('Container "{0}" cannot be connected to network "{1}" as it is not running.'
                 .format(container,network.name))
    return

def detach_container_from_network(endpoint, container, network_id):
    log=logging.getLogger('pk_docker')
    client = docker.DockerClient(base_url=client_address, version=client_version)
    network = client.networks.get(network_id)
    if client.containers.get(container).status == "running":
        network.disconnect(container)
        log.info('Container "{0}" is disconnected from network "{1}".'.format(container, network.name))
    else:
        log.info('Container "{0}" cannot be disconnected from network "{1}" as it is not running.'
                 .format(container,network.name))
    return
    


