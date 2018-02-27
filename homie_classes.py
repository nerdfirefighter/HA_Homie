// VERY Work In Progress

HomieDevices[device_id] = HomieDevice()

HomieMessages[string] = string



class HomieDevice(Object):
    
    def __init__(self, device_id, topics[], parent_base='devices'):
        self._device_id = device_id
        self._topic_base = parent_base + '/' + device_id
        
        self._name = topics[self._topic_base + '/$name']
        self._conventionVersion = topics[self._topic_base + '/$homie']
        self._state = topics[self._topic_base + '/$online']
        self._ip = topics[self._topic_base + '/$ip']
        self._mac = topics[self._topic_base + '/$mac']

        self._uptime = topics[self._topic_base + '/$stats/uptime']
        self._signal = topics[self._topic_base + '/$stats/signal']
        self._statsInterval = topics[self._topic_base + '/$stats/interval']
        self._fw_name = topics[self._topic_base + '/$fw/name']
        self._fw_version = topics[self._topic_base + '/$fw/version']
        self._fw_checksum = topics[self._topic_base + '/$fw/checksum']

        self._nodes[] = {}
        for node in topics[self._topic_base + '/$nodes'].split(','):
            self._nodes[node] = HomieNode(node, topics, self._topic_base)




class HomieNode(Object):

    def __init__(self, node_id, topics[], parent_base):

        self._node_id = node_id
        self._topic_base = parent_base + '/' + node_id
        self._type = topics[self._topic_base + '/$type']
        self._name = topics[self._topic_base + '/$name']


        self._properties[] = {}
        for property in topics[self._topic_base + '/$properties'].split(','):
            self._properties[property] = HomieProperty(property, topics, self._topic_base)




class HomieProperty (Object)

    def __init__(self, property_id, topics[], parent_base):
    
        self._property_id = property_id
        self._topic_base = parent_base + '/' + property_id
        self._settable = topics[self._topic_base + '/$settable']

        self._unit = topics[self._topic_base + '/$unit']
        self._datatype topics[self._topic_base + '/$datatype']
        self._name = topics[self._topic_base + '/$name']
        self._format = topics[self._topic_base + '/$format']








