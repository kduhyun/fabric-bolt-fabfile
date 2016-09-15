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
