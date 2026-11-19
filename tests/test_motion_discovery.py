"""Exercise first Security+ 2.0 motion discovery with the real firmware handlers."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MotionDiscoveryTest(unittest.TestCase):
    def test_first_motion_persists_and_publishes_without_a_reboot(self):
        homekit = (ROOT / "src/homekit.cpp").read_text()
        comms = (ROOT / "src/comms.cpp").read_text()
        accessory = homekit.split("bool enable_service_homekit_motion_sensor(bool enable)\n", 1)[1]
        accessory = accessory.split("bool enable_service_homekit_stop", 1)[0]
        discovery = homekit.split("void enable_service_homekit_motion(bool reboot)\n", 1)[1]
        discovery = discovery.split("void notify_homekit_motion", 1)[0]
        packet = comms.split("case PacketCommand::Motion:", 1)[1].split("case PacketCommand::DoorAction:", 1)[0]
        source = r'''
#include <cassert>
#define ESP32
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGD(...) ((void)0)
#define ESP8266_SAVE_CONFIG() ((void)0)
constexpr int cfg_motionTriggers=1, nvram_has_motion=2, HOMEKIT_AID_MOTION=3;
struct { bool has_motion_sensor=false, light=false, motion=false; } garage_door;
struct { struct { bool motion=false; } bit; int asInt=0; } motionTriggers;
struct Config {
    bool enabled=true;
    bool getMotionHomeKit() { return enabled; }
    int getMotionTriggers() { return motionTriggers.bit.motion; }
    void set(int key, int) { assert(key==cfg_motionTriggers && motionTriggers.bit.motion); }
} config, *userConfig=&config;
int saved=0, publications=0, notifications=0;
bool paused=false;
int *motion=nullptr;
struct Pause {
    Pause() { assert(!paused); paused=true; }
    ~Pause() { paused=false; }
};
#define homeSpanPAUSE Pause pause;
struct {
    void updateDatabase() { assert(paused && motion); ++publications; }
    bool deleteAccessory(int) { return true; }
} homeSpan;
void createMotionAccessories() { assert(paused); motion=&publications; }
void enable_service_homekit_room_occupancy(bool) {}
void write_door_int(int key, int value) { assert(key==nvram_has_motion && value==1); ++saved; }
void sync_and_restart() { assert(false && "discovery should not restart"); }
void send_get_status() {}
void notify_homekit_motion(bool state) { assert(state); garage_door.motion=state; if (motion) ++notifications; }
''' + "bool enable_service_homekit_motion_sensor(bool enable)\n" + accessory + (
            "void enable_service_homekit_motion(bool reboot)\n" + discovery
            + "enum class PacketCommand { Motion };\nvoid event() { switch (PacketCommand::Motion) {"
            + "case PacketCommand::Motion:" + packet + "} }\n"
        ) + r'''
int main() {
    event();
    assert(garage_door.has_motion_sensor && saved==1 && publications==1 && notifications==1 && !paused);
    event();
    assert(saved==1 && publications==1 && notifications==2);
    garage_door.has_motion_sensor=false;
    motion=nullptr;
    config.enabled=false;
    event();
    assert(garage_door.has_motion_sensor && saved==2 && publications==1 && notifications==2);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "motion.cpp"
            binary = Path(directory) / "motion"
            path.write_text(source)
            subprocess.run(["c++", "-std=c++17", str(path), "-o", str(binary)], check=True, timeout=60)
            subprocess.run([str(binary)], check=True, timeout=10)
