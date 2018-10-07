import os
import sys
import logging

import paramiko
#TODO:Improve parsing!
logger=logging.getLogger(__name__)

class Command:
    def __init__(self, cmdline):
        cmd=cmdline.split(":")
        self.name=cmd[0]
        self.args=cmd[1:]
    def run(self, context, *args, **kwargs):
        pass

class Script:
    commands=[]
    def __init__(self,context):
        self.data=context
    def run(self):
        for command in self.commands:
            self.data.update(command.run(self.data))
###ALL COMMANDS###
class ConnectCommand(Command):
    def run(self, context, *args, **kwargs):
        if len(self.args)>=4:
            username=self.args[0]
            password=self.args[1]
            host=self.args[2]
            port=int(self.args[3])
        else:
            host=context["HOST"]
            port=int(context["PORT"])
            username=context["USERNAME"]
            password=context["PASSWORD"]
        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host,username=username,password=password,port=port)
        return {"client":client}

class CloseCommand(Command):
    def run(self, context, *args, **kwargs):
        if "client" in context:
            context["client"].close()
        else:
            logger.error("Could not close connection.No open connections right now.")
        return dict() #Empty dict

class ExecCommand(Command):
    def __init__(self, line):
        self.args=[line]
    def run(self, context, *args, **kwargs):
        #if "client" in context:
        stdin, stdout, stderr = context["client"].exec_command(self.args[0])
        return {"stdin":stdin,"stdout":stdout,"stderr":stderr}

class DumpStdOutCommand(Command):#FIXME:All prechecks
    def run(self, context, *args, **kwargs):
        if len(self.args)<1:
            logger.error("DUMPSTDOUT:requres an argument")
            return dict()
        with open(self.args[0],"wb") as f:
            f.write(context["stdout"].read())
        return dict()

commands={"CONNECT_SSH":ConnectCommand,"DUMPSTDOUT":DumpStdOutCommand,"CLOSE_SSH":CloseCommand}
class Config:
    def __init__(self,fname):
        context=dict()
        f=open(fname)
        line=f.readline()
        while line:
            line = line.split("#")[0]
            line=line.rstrip("\n")
            if line=="!SCRIPT":
                script=Script(context)
                while line and line!="!END":
                    line=f.readline()
                    line=line.rstrip("\n")
                    if line=="!END":
                        break
                    if line=="":
                        continue
                    if line[0]=="!":
                        line=line[1:]
                        cmdname=line.split(":")[0]
                        cmd=commands[cmdname](line)
                        script.commands.append(cmd)
                    else:
                        script.commands.append(ExecCommand(line))
                script.run()
            if line=="":
                continue
            if line!="!END":
                key, value = line.split(":")
                context.update({key: value})
            line=f.readline()
        f.close()

def main():
    for config in os.listdir("/etc/autobackup"):
        Config(config)

if __name__=='__main__':
    main()
