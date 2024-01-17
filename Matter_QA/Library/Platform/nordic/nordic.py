import datetime
import traceback
import time
import logging
import os
from threading import Event, Thread
import sys
from mobly import signals
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import BaseDutNodeClass, BaseNodeDutConfiguration
from ..serial import SerialPort

event_closer = Event()


class NordicDut(BaseDutNodeClass, BaseNodeDutConfiguration):
    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config
        self.serial_port_obj = SerialPort(port=self.test_config["nordic_config"]["serial_port"],
                       baudrate=self.test_config["nordic_config"]["serial_baudrate"],
                       timeout=self.test_config["nordic_config"]["serial_timeout"]).create_serial()

    def reboot_dut(self):
        pass

    def factory_reset_dut(self, stop_reset: bool):
        if not stop_reset:
            # self.stop_logging()
            for i in range(1, 4):
                logging.info("resetting nordic matter device")
                self.serial_port_obj.write_cmd(b'matter device factoryreset\n')
                time.sleep(2)
            self.serial_port_obj.close()
            return True
        else:
            self.start_matter_app()
            logging.info("completed advertising of DUT")
            return True

    def start_matter_app(self):
        SerialPort(port=self.test_config["nordic_config"]["serial_port"],
                   baudrate=self.test_config["nordic_config"]["serial_baudrate"],
                   timeout=self.test_config["nordic_config"]["serial_timeout"]).write_cmd()
        time.sleep(2)
        return True

    def start_logging(self, log=None) -> bool:
        global event_closer
        if self.test_config["current_iteration"] == 0:
            self.test_config["current_iteration"] += 1

        if self.serial_port_obj.is_open:
            while self.serial_port_obj.is_open:
                try:
                    current_dir = self.test_config["iter_logs_dir"]
                    log_path = os.path.join(current_dir, str(self.test_config["current_iteration"]))
                    if not os.path.exists(log_path):
                        os.mkdir(log_path)
                    log_file = os.path.join(log_path, "Dut_log_{}_"
                                            .format(str(self.test_config["current_iteration"])) +
                                            str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                            + ".log"
                                            )
                    logging.info("started to read buffer")
                    data = self.serial_port_obj.read_until(b'Done\r\r\n').decode()
                    logging.info("completed read from buffer")
                    if data == '':
                        logging.info("data not present in buffer breaking from read loop")
                        break
                    with open(log_file, 'w') as fp:
                        fp.write(data)
                        logging.info("completed write to file")

                except Exception as e:
                    print(e)
                    traceback.print_exc()
        else:
            logging.info("Failed to read the log in thread")
            sys.exit()
        logging.info("closing the Log File")
        return True

    def stop_logging(self):
        global event_closer
        event_closer.set()
        return True


def create_dut_object(test_config):
    dut_obj = NordicDut(test_config=test_config)
    thread = Thread(target=dut_obj.start_logging)
    thread.start()
    dut_obj.factory_reset_dut(stop_reset=False)
    return dut_obj
