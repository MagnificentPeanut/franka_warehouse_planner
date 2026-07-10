#!/bin/bash
pkill -f ign-gazebo; pkill -f ruby; sleep 2
ign gazebo -r -s test_detachable.sdf > /tmp/ign.log 2>&1 &
IGN_PID=$!
sleep 5
echo "Attaching..."
ign topic -t "/box/attach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
echo "Detaching..."
ign topic -t "/box/detach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
echo "Attaching again..."
ign topic -t "/box/attach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
echo "Detaching again..."
ign topic -t "/box/detach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
kill $IGN_PID
grep -i "detachable" /tmp/ign.log
