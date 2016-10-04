wget https://raw.githubusercontent.com/kduhyun/fabric-bolt-fabfile/master/master/haproxy.cfg.template -O /etc/haproxy/haproxy.cfg.template

touch /etc/haproxy/haproxy.cfg
mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.old
cat /etc/haproxy/haproxy.cfg.template > /etc/haproxy/haproxy.cfg
mysql -u owltree -h owltreedb.internal owltree -e "select concat('    server ','app',instanceId,' ',internalIp,':8080 check') from ServerList where useYN<>'N'" | grep -v concat >> /etc/haproxy/haproxy.cfg

diff=`cmp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.old | wc -l`

if [ "$diff" != "0" ]; then
	service haproxy reload
fi
