#!/bin/bash

sudo docker exec guacamole_compose /bin/bash -c "cp /tmp/guacconf/web.xml /usr/local/tomcat/conf/web.xml && cp /tmp/guacconf/error.jsp /usr/local/tomcat/webapps/guacamole/error.jsp && rm -rf /usr/local/tomcat/webapps/ROOT && rm -rf /usr/local/tomcat/webapps/docs && rm -rf /usr/local/tomcat/webapps/examples && rm -rf /usr/local/tomcat/webapps/host-manager && rm -rf /usr/local/tomcat/webapps/manager"
