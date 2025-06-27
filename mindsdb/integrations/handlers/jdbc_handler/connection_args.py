# 文件名: connection_args.py
from collections import OrderedDict
from mindsdb.integrations.libs.const import HANDLER_CONNECTION_ARG_TYPE as ARG_TYPE

connection_args = OrderedDict(
    connection_string={
        'type': ARG_TYPE.STR,
        'description': 'The full JDBC connection string (URL) for the target database. E.g., for Hive with ZooKeeper: "jdbc:hive2://zk_node1:2181,.../;serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2"',
        'required': True,
        'label': 'Connection String'
    },
    user={
        'type': ARG_TYPE.STR,
        'description': 'The username for the database.',
        'required': True,
        'label': 'Username'
    },
    password={
        'type': ARG_TYPE.PWD,
        'description': 'The password for the database.',
        'secret': True,
        'required': False,
        'label': 'Password'
    },
    driver_class_name={
        'type': ARG_TYPE.STR,
        'description': 'The fully qualified class name of the JDBC driver. E.g., "org.apache.hive.jdbc.HiveDriver"',
        'required': True,
        'label': 'Driver Class Name'
    },
    jdbc_driver_path={
        'type': ARG_TYPE.STR,
        'description': 'The absolute path to the directory containing all required .jar files for the JDBC driver.',
        'required': True,
        'label': 'JDBC Driver Directory Path'
    }
)

connection_args_example = OrderedDict(
    connection_string='jdbc:hive2://**/;serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2',
    user='your_user',
    password='your_password',
    driver_class_name='org.apache.hive.jdbc.HiveDriver',
    jdbc_driver_path='/path/to/your/jars/'
)