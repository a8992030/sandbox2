import subprocess
import tempfile

def run_script(script):
    # print(script)
    with tempfile.NamedTemporaryFile('w') as script_file:
        script_file.write(script)
        script_file.flush()
        pipe = subprocess.Popen(['/bin/bash', script_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        return out, err, pipe.returncode