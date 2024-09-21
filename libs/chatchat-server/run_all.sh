nohup python -u chatchat/cli.py start -a > log_run_all.txt 2>&1 &
tail -f -n 100 log_run_all.txt

