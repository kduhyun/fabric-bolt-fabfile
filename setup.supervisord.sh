instance_place=`wget -qO- http://instance-data/latest/meta-data/placement/availability-zone`
instance_place_2=`echo ${instance_place:0:2}`
instance_id=`wget -qO- http://instance-data/latest/meta-data/instance-id`
server_id=`echo "${instance_place:0:2}${instance_id:2}"`

if [ "$instance_place_2" = "us" ]; then
    PROFILES="production,virginia,worker,serverid"
elif [ "$instance_place_2" = "ap" ]; then
    PROFILES="production,seoul,serverid"
fi

PROFILES=${PROFILES}${server_id}

echo $PROFILES

mkdir -p /svc/

curl https://raw.githubusercontent.com/kduhyun/fabric-bolt-fabfile/master/supervisord.conf.template | sed s/_PROFILES_/${PROFILES}/g > /svc/supervisord.conf
