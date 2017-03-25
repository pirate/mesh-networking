import sys
from io import StringIO
from subprocess import Popen, PIPE, STDOUT

def run_cmd(command, verbose=True, shell='/bin/bash'):
    """internal helper function to run shell commands and get output"""
    process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT, executable=shell)
    output = process.stdout.read().decode().strip().split('\n')
    if verbose:
        # return full output including empty lines
        return output
    return [line for line in output if line.strip()]

def run_python(cmd, timeout=60):
    """interactively interpret recieved python code"""
    try:
        try:
            buffer = StringIO()
            sys.stdout = buffer
            exec(cmd)
            sys.stdout = sys.__stdout__
            out = buffer.getvalue()
        except Exception as error:
            out = error

        out = str(out).strip()

        if len(out) < 1:
            try:
                out = "[eval]: "+str(eval(cmd))
            except Exception as error:
                out = "[eval]: "+str(error)
        else:
            out = "[exec]: "+out

    except Exception as python_exception:
        out = "[X]: %s" % python_exception

    return out.strip()

def run_shell(cmd, timeout=60, verbose=False):
    """run a shell command and return the output, verbose enables live command output via yield"""
    retcode = None
    try:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT, executable='/bin/bash')
        continue_running = True
    except Exception as e:
        yield("Failed: %s" % e)
        continue_running = False

    while continue_running:
        try:
            line = p.stdout.readline()
            if verbose and line:
                yield(line)
            elif line.strip():
                yield(line.strip())
        except Exception:
            pass

        try:
            data = irc.recv(4096)
        except Exception as e:
            data = ""
            retcode = p.poll()  # returns None while subprocess is running

        if '!cancel' in data:
            retcode = "Cancelled live output reading. You have to kill the process manually."
            yield "[X]: %s" % retcode
            break

        elif retcode is not None:
            try:
                line = p.stdout.read()
            except:
                retcode = "Too much output, read timed out. Process is still running in background."

            if verbose and line:
                yield line

            if retcode != 0:
                yield "[X]: %s" % retcode
            elif retcode == 0 and verbose:
                yield "[√]"

            break
