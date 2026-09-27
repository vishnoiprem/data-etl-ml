import os, subprocess, sys
env = os.environ.copy()
env["PYTHONPATH"] = "/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/datavidhya/22_Build_Visual_ETL_Pipeline_With_Glue_Studio"
p = subprocess.run([sys.executable, "/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/datavidhya/22_Build_Visual_ETL_Pipeline_With_Glue_Studio/glue_jobs/customer_etl_glue_studio.py", "/tmp/raw", "/tmp/q22_out2"], capture_output=True, text=True, env=env)
print("RC:", p.returncode)
print("STDERR:", p.stderr)
print("STDOUT:", p.stdout)
