# -*- coding: utf-8 -*-
"""
LOF基金溢价监控程序 - 主入口
"""

import argparse
from cli import LOFMonitorCLI
from ui import run_app

def main():
    parser = argparse.ArgumentParser(description="LOF基金溢价监控系统")
    parser.add_argument("-t", "--terminal", action="store_true", help="Run in terminal mode (CLI)")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.terminal or args.run_once:
        cli = LOFMonitorCLI()
        if args.run_once:
            cli.run_monitor_cycle()
        else:
            cli.start()
    else:
        run_app()

if __name__ == "__main__":
    main()
