#!/bin/bash
pkill -f ign-gazebo; sleep 1
ign gazebo -r -s test_detachable_spawn.sdf > /tmp/ign.log 2>&1 &
IGN_PID=$!
sleep 5
echo "Spawning arm..."
ign service -s /world/test_world/create --reqtype ignition.msgs.EntityFactory --reptype ignition.msgs.Boolean --timeout 3000 --req 'sdf: "<sdf version=\"1.6\"><model name=\"arm\"><pose>0 0 1 0 0 0</pose><link name=\"link\"><collision name=\"c\"><geometry><sphere><radius>0.1</radius></sphere></geometry></collision></link></model></sdf>"'
sleep 3
echo "Attaching..."
ign topic -t "/box/attach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
echo "Detaching..."
ign topic -t "/box/detach" -m ignition.msgs.Empty -p "unused: true"
sleep 2
kill $IGN_PID
grep -i "detachable" /tmp/ign.log
