#!/bin/bash -e
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

function run_mocked_pipeline_server {
    if [ -d "/home/vagrant/test" ]; then
        echo "tcp-mocker installation exists and running it ......" 
    else
        mkdir -p  /home/vagrant/mock-pipeline-server
	    cd /home/vagrant/mock-pipeline-server
        if ! [ -x "$(command -v git)" ]; then
            sudo apt-get -y install git
        fi
	    git clone https://github.com/payworks/tcp-mocker.git
	    cd tcp-mocker/
	    if [[ "$(docker images -q tcpmocker/tcp-mocker-app:LOCAL-SNAPSHOT 2> /dev/null)" == "" ]]; then
            if ! [ -x "$(command -v docker-compose)" ]; then
                sudo apt-get -y install docker-compose
            fi
            docker-compose up
        fi
    fi
    echo  "\n -----Running mock server substituting pipeline server -----\n"    
	docker run --tty --rm  -p 8000:10001  tcpmocker/tcp-mocker-app:LOCAL-SNAPSHOT 
}

run_mocked_pipeline_server
