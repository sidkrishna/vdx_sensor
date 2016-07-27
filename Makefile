help:
	@echo "  package     creates a tar.gz file"
	@echo "  deploy     deploys pack on a remote StackStorm, requires arguments user=<your_username> and destination=<ip>"

package:
	rm -f vdxsensor.tar.gz; tar -zcvf vdxsensor.tar.gz --exclude='.git' --exclude='venv' --exclude='Makefile' --exclude='vdxsensor.tar.gz' -C .. ./vdx_sensor

deploy:
	make package && \
	cat ./vdxsensor.tar.gz | ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no $(user)@$(destination) \
	"cd /opt/stackstorm/packs; tar -zxvf -; chown -R root:st2packs /opt/stackstorm/packs/*; \
	st2 auth -t -p st2admin st2admin > /tmp/st2_token; sed -i 's/^/export ST2_AUTH_TOKEN=/g' /tmp/st2_token; \
	source /tmp/st2_token; \
	st2 run packs.load register=all; \
	st2 run packs.restart_component servicename=st2sensorcontainer"
