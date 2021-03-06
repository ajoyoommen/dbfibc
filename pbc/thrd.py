import threading
import time
import socket
import re
import string
import sys
from ctypes import *

nodeID = 1; identity = ""; tempcontlist = []; port = 1000; numNodes = 0;ip = '127.0.0.1'; sys_n = 1; sys_t = 1; sys_f = 1
ibc = cdll.LoadLibrary('./libibc.so.1.0.1')

def read_contlist():
  """contlist contains the node contact addresses, load it into a list"""
  fp = open("contlist", "r")
  global tempcontlist, numNodes
  """reading from contlist and adding it to list tempcontlist for searching...
  tempcontlist[1] contains the contact details for node 3, and so on.
  tempcontlist[1] is again a list where each index represents
  - - - - 0:nodeID, 1:Ip addr, 2:Port num, 3:cert file for tls,
  - - - - 4:optional L to identify the leader
  numNodes tracks the total entries in contlist"""
  while 1:
    line = fp.readline()
    if not line:
      break
    numNodes += 1
    parse = re.search("([\S]+)\s([\S]+)\s([\S]+)\s([\S]+)\s([L]*)", line)
    tempcontlist.append([parse.group(1), parse.group(2), parse.group(3), parse.group(4), parse.group(5)])
  fp.close()
  """Easiest way to retreive from tempcontlist
  jl = tempcontlist[int(nodeID)-1]
  print jl[2]"""

def read_identity():
  """identity contains the node ID in line 1 and the user ID in line 2"""
  fp = open("identity", "r")
  global nodeID, identity
  n = fp.readline()
  nodeID = n.rstrip('\r\n')
  i = fp.readline()
  #identity = i.rstrip('\r\n')
  fp.close()
  
def read_sysparam():
  """This function will read system.param and initialize the values for n, t, f"""
  global sys_n, sys_t, sys_f
  fp = open("system.param","r")
  n = fp.readline()
  t = fp.readline()
  f = fp.readline()
  fp.close()
  n = n.rstrip('\r\n')
  t = t.rstrip('\r\n')
  f = f.rstrip('\r\n')
  pr = re.search("(n)\s(\d)", n)
  if pr==None:
    print("Corrupted system.param(n). About to quit.")
    sys.exit()
  else:
    sys_n = int(pr.group(2))
  pr = re.search("(t)\s(\d)", t)
  if pr==None:
    print("Corrupted system.param(t). About to quit.")
    sys.exit()
  else:
    sys_t = int(pr.group(2))
  pr = re.search("(f)\s(\d)", f)
  if pr==None:
    print("Corrupted system.param(t). About to quit.")
    sys.exit()
  else:
    sys_f = int(pr.group(2))
    
def listen():
  """This socket will listen for IBCRequests and IBCReply messages"""
  global port, ip
  servsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    servsock.bind(('', int(port)))
  except Exception, e:
    print "Error : ", e
  servsock.listen(5)
  while True:
    #print "Waiting for connection"
    conn, address = servsock.accept()
    #print "connection from ", address
    #print "Waiting for message"
    msg = conn.recv(2048)
    parse_msg(msg)
    print "Length of message received is ", len(msg)
  conn.close()
  servsock.close()
  return

def ibc_request_recv(stringid, nid):
  """On receiving an IBC_REQUEST, this will use PBC to hash^share the recvd ID
  and send it to the node from a new socket"""
  global tempcontlist
  print "1"
  c_id = (c_char * 40)()
  print "2"
  c_id.value = stringid
  print "3"
  ibc.hash_id_s(c_id)
  print "4"
  hsid = (c_ubyte * 128).in_dll(ibc, "hid")
  print "5"
  ibcreply = (c_char * 128).from_buffer(hsid).value
  print "6"
  i = int(nid) - 1
  [nodeid, c_ip, c_port, cert_file, l] = tempcontlist[i]
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sock.connect((c_ip, int(c_port)))
  except Exception, e:
    print "Unable to send : ", e, c_ip, c_port
    return
  msg = "IBC_REPLY:" + ibcreply + ":" + nodeID + ":END"
  print "Sent (", len(msg), " bytes) : ", msg
  sock.sendall(msg)
  sock.close()

def ibc_reply_recv(ibcreply, sender):
  uchar = (c_ubyte * 128)(*map(ord, ibcreply))
  ibc.gen_privatekey(uchar, nodeID, sender)
  #sys.exit()
  
def parse_msg(msgstr):
  parse = re.search("([\w]+):(.*)", msgstr)
  if parse == None:
    print "Received invalid message : ", msgstr
  elif parse.group(1) == "IBC_REQUEST":
    parseid = re.search("([\S]+):([\S]+)(:END)", parse.group(2))
    if parseid == None:
      print "Invalid IBC request : ", parse.group(2)
    else:
      print "Received : IBC request for the id ", parseid.group(1) + " from " + parseid.group(2)
      ibc_request_recv(parseid.group(1), parseid.group(2))
  elif parse.group(1) == "IBC_REPLY":
    parseid = re.search("([\S]+):([\S]+)(:END)", parse.group(2))
    if parseid == None:
      print "Received invalid IBC_REPLY : ", parse.group(2)
      #sys.exit()
    else:
      print "Received IBC_REPLY from ", parseid.group(2)
      ibc_reply_recv(parseid.group(1), parseid.group(2))

def sendRequest():
  """This socket will send IBC_REQUEST messages"""
  global tempcontlist, numNodes, nodeID, port
  for i in range(numNodes):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    [nodeid, c_ip, c_port, cert_file, l] = tempcontlist[i]
    if c_port == port:
      continue
    #print "i ", nodeID, "am trying to connect to ", nodeid, "at ", c_ip, int(c_port), c_port
    try:
      sock.connect((c_ip, int(c_port)))
    except Exception, e:
      print "Unable to send : ", e, c_ip, c_port
      continue;
    msg = "IBC_REQUEST:" + identity + ":" + nodeID + ":END"
    print "Sent : ", msg
    sock.sendall(msg)
    sock.close()
  return
  
def init_pbc():
  read_contlist()
  read_identity()
  read_sysparam()
  ibc.init_pairing(sys_n, sys_t, sys_f)
  print "Py : n is ", sys_n, "t is ", sys_t, "f is ", sys_f
  ibc.read_share()

def main(userid):
  global port, ip, nodeID, identity
  init_pbc()
  identity = userid
  li = tempcontlist[int(nodeID) - 1]
  ip = li[1]
  port = li[2]
  threading.Thread(target=listen).start()
  option = input("Enter 1 to send request : ")

  if option == 1:
    threading.Thread(target=sendRequest).start()

  """r = input("Which row do you wish to print : ")
  r = r - 1
  print tempcontlist[r]"""

  
if __name__ == "__main__":
  main()