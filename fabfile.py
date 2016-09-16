from fabric.api import *

env.user='ec2-user'
env.key_filename=['/home/ec2-user/.ssh/owltree.pem']

def build():
    run("cd /svc/git/owltreeserver && git pull")
    run("cd /svc/git/owltreeserver && git pull && git checkout develop && ./mvnw install && rm -f /svc/git/owltreeserver/target/OwlTree-1.0.0.zip && zip -9 -j /svc/git/owltreeserver/target/OwlTree-1.0.0.zip /svc/git/owltreeserver/target/OwlTree-1.0.0.jar && s3cmd put --force /svc/git/owltreeserver/target/OwlTree-1.0.0.zip s3://owltree/")

def deploy():
    run("echo "+env.host)
    run("echo lb_out")
    with settings(warn_only=True):
        run("s3cmd get --force s3://owltree/OwlTree-1.0.0.zip /svc/owltree/ && cd /svc/owltree/ && unzip -o ./OwlTree-1.0.0.zip")
        sudo("ps aux | grep OwlTree-1.0.0.jar | grep -v grep | awk '{print $2}' | xargs kill && sleep 5")

def local():
    build()
    deploy()

def test():
    run("echo "+env.host)

def setup():
    run("echo 'step 1. make default directories.'")
    sudo("mkdir -p /svc/owltree && chown ec2-user.ec2-user /svc && chown ec2-user.ec2-user /svc/*")

    run("echo 'step 2. install jdk 1.8'")
    run('cd /svc && wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/8u101-b13/jdk-8u101-linux-x64.tar.gz"')
    run("cd /svc && tar xzf jdk-8u101-linux-x64.tar.gz")
    run("ln -s /svc/jdk1.8.0_101 /svc/java")
    sudo("mv /usr/bin/java /usr/bin/java_bak")
    sudo("ln -s /svc/java/bin/java /usr/bin/java")

    run("echo 'step 3. increase file limits'")
    sudo("sed -i '$ a\* - memlock unlimited\n* - nofile 100000\n* - nproc 32768\n* - as unlimited' /etc/security/limits.conf")

    run("echo 'step 4. set up supervisord.conf'")
    run("cd /svc && wget https://raw.githubusercontent.com/kduhyun/fabric-bolt-fabfile/master/setup.supervisord.sh && sh /svc/setup.supervisord.sh")
    
    run("echo 'step 5. set up swap memories")
    sudo("dd if=/dev/zero of=/swapfile bs=1M count=1024 && chown root:root /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && swapon -a && sed -i '$ a\swap        /swapfile   swap   swap   defaults  0  0' /etc/fstab")
    
    run("echo 'step 6. add an public key for owltree.pem")
    run("echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCaQu9A7OSGw8l1uEHx3MN6xHRmNSb5vZDZCadu0GlRoQig8V2bqCFRuIKWv7VXwFDq9oywtPQjPMh1Je2z7uIPHEtGTl1N6dS5u6d9thfxhbBz4yWLtLzT31V8p5Y0Rq8WgiVQV0QAfCFpSCaKTPavXoiKbfSdfPCpCF7lNgLzrQnL7LcvPpHxtjzTBgYBrITDlRQCdCktqXvzi6hGq0++SfvF2QpJ4r9MtqxP1CDbks5Ir8cHRZPeXb+F088uaygaVXpe3s7b5/8NHh8IjyV2fFZpiiDj49VvTuMoxv2iLhC1j3/Wd9pUEaTUVk4buSlf7H69yOYu9c/MGRX5KIX1 owltree' >> ~/.ssh/authorized_keys")
