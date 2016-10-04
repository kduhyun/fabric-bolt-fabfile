from fabric.api import *

env.user='ec2-user'
env.key_filename=['/home/ec2-user/.ssh/owltree.pem', '/home/ec2-user/.ssh/choco.pem']
env.warn_only=True

def build():
    run("cd /svc/git/owltreeserver && git pull")
    run("cd /svc/git/owltreeserver && git pull && git checkout develop && ./mvnw install && rm -f /svc/git/owltreeserver/target/OwlTree-1.0.0.zip && zip -9 -j /svc/git/owltreeserver/target/OwlTree-1.0.0.zip /svc/git/owltreeserver/target/OwlTree-1.0.0.jar && s3cmd put --force /svc/git/owltreeserver/target/OwlTree-1.0.0.zip s3://owltree/")

def processDeploying():    
    with settings(warn_only=True):
        run("s3cmd get --force s3://owltree/OwlTree-1.0.0.zip /svc/owltree/ && cd /svc/owltree/ && unzip -o ./OwlTree-1.0.0.zip")
        sudo("ps aux | grep OwlTree-1.0.0.jar | grep -v grep | awk '{print $2}' | xargs kill && sleep 5")
    
def deploy():
    run("echo "+env.host)
    ("echo 'lb_out' && curl 'http://localhost:8080/util/status/off' && sleep 30")
    processDeploying()
    run("echo 'lb_in' && sleep 60 && curl 'http://localhost:8080/util/status/on'")

@parallel(pool_size=5)
def deployParallel():
    run("echo '"+env.host +"' && date")
    
    run("echo 'lb_out' && curl 'http://localhost:8080/util/status/off' && sleep 30")
    processDeploying()
    run("echo 'lb_in' && sleep 60 && curl 'http://localhost:8080/util/status/on'")
        
def local():
    build()
    deploy()

@parallel(pool_size=2)
def test():
    run("echo "+env.host)

def setup():
    run("echo 'step 1. make default directories.'")
    sudo("mkdir -p /svc/owltree && chown ec2-user.ec2-user /svc && chown ec2-user.ec2-user /svc/*")
    put('/svc/owltree/*.y*ml','/svc/owltree')

    run("echo 'step 2. install jdk 1.8'")
    isJava8=run("java -version 2>&1 | grep '1.8.0' | wc -l")
    if int(isJava8) == 0:
        run('cd /svc && wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/8u101-b13/jdk-8u101-linux-x64.tar.gz"')
        run("cd /svc && tar xzf jdk-8u101-linux-x64.tar.gz")
        run("ln -s /svc/jdk1.8.0_101 /svc/java")
        sudo("mv /usr/bin/java /usr/bin/java_bak")
        sudo("ln -s /svc/java/bin/java /usr/bin/java")

    
    run("echo 'step 3. increase file limits'")
    isNofileAppended=run("cat /etc/security/limits.conf | grep 'nofile 100000' | wc -l")
    if int(isNofileAppended) == 0:
        sudo("sed -i '$ a\* - memlock unlimited\\n* - nofile 100000\\n* - nproc 32768\\n* - as unlimited' /etc/security/limits.conf")

    run("echo 'step 4. set up supervisord.conf'")
    isSupervisorOk=run("which supervisorctl | wc -l")
    if isSupervisorOk != "1":
        run("cd /svc && rm -f /svc/setup.supervisord.sh* && wget https://raw.githubusercontent.com/kduhyun/fabric-bolt-fabfile/master/setup.supervisord.sh && sh /svc/setup.supervisord.sh")
        sudo("ln -s /svc/supervisord.conf /etc/supervisord.conf")
        sudo("pip install supervisor")
        sudo("cd /etc/init.d && wget https://raw.githubusercontent.com/kduhyun/fabric-bolt-fabfile/master/supervisor && chmod 755 /etc/init.d/supervisor")
        sudo("ln -s /usr/local/bin/supervisorctl /usr/bin/")
        sudo("service supervisor start")
    
    run("echo 'step 5. set up swap off memories'")
    isSwapOn=run("cat /etc/sysctl.conf | grep swappiness | wc -l")
    if int(isSwapOn) == 0:
        sudo("echo 'vm.swappiness = 0' >> /etc/sysctl.conf")
    
    #run("echo 'step 5. set up swap off memories'")
    #isSwapOn=run("swapon -s | wc -l")
    #if int(isSwapOn) == 0:
    #    sudo("dd if=/dev/zero of=/swapfile bs=1M count=1024")
    #    sudo("chown root:root /swapfile")
    #    sudo("chmod 600 /swapfile")
    #    sudo("mkswap /swapfile")
    #    sudo("swapon /swapfile")
    #    sudo("swapon -a")
    #    sudo("sed -i '$ a\swap        /swapfile   swap   swap   defaults  0  0' /etc/fstab")
    #    sudo("vm.swappiness = 0 >> /etc/sysctl.conf")
    
    run("echo 'step 6. add an public key for owltree.pem'")
    isKeyAppended=run("cat ~/.ssh/authorized_keys | grep owltree | wc -l")
    if int(isKeyAppended) == 0:
        run("echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCaQu9A7OSGw8l1uEHx3MN6xHRmNSb5vZDZCadu0GlRoQig8V2bqCFRuIKWv7VXwFDq9oywtPQjPMh1Je2z7uIPHEtGTl1N6dS5u6d9thfxhbBz4yWLtLzT31V8p5Y0Rq8WgiVQV0QAfCFpSCaKTPavXoiKbfSdfPCpCF7lNgLzrQnL7LcvPpHxtjzTBgYBrITDlRQCdCktqXvzi6hGq0++SfvF2QpJ4r9MtqxP1CDbks5Ir8cHRZPeXb+F088uaygaVXpe3s7b5/8NHh8IjyV2fFZpiiDj49VvTuMoxv2iLhC1j3/Wd9pUEaTUVk4buSlf7H69yOYu9c/MGRX5KIX1 owltree' >> ~/.ssh/authorized_keys")

    run("echo 'step 7. set up s3cmd'")
    isS3cmdOk=run("ls ~/.s3cfg | wc -l")
    if isS3cmdOk != "1":
       sudo("pip install s3cmd")
       put('/home/ec2-user/.s3cfg', '/home/ec2-user/.s3cfg')

    run("echo 'step 8. set up /etc/hosts'")
    isHostsOk=sudo("cat /etc/hosts | grep owltree | wc -l")
    if int(isHostsOk) == 0:
        sudo("echo '172.30.0.10 infra infra.owltree.us' >> /etc/hosts")

        
    run("echo 'step 9. set up aliases.'")
    isAliasOk=sudo("cat /home/ec2-user/.bash_profile | grep alias | wc -l")
    if int(isAliasOk) == 0:
        run("""echo "alias log='sudo supervisorctl tail -f owl'" >> /home/ec2-user/.bash_profile""")
        sudo("""echo "alias log='supervisorctl tail -f owl'" >> /root/.bash_profile""")
    
    run("echo 'step 10. deploying Jar.'")
    processDeploying()
    sudo("service supervisor restart")
