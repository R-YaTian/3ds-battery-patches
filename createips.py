#!/usr/bin/env python

import os
import struct
import subprocess
from contextlib import suppress
from shutil import copy2, copystat, Error

def copytree(src, dst, symlinks=False, ignore=None, copy_function=copy2,
             ignore_dangling_symlinks=False, dirs_exist_ok=False):
    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []

    for srcentry in os.scandir(src):
        if ignore is not None:
            ignored_names = ignore(src, srcentry.name)
        else:
            ignored_names = set()
        if srcentry.name in ignored_names:
            continue
        srcname = os.path.join(src, srcentry.name)
        dstname = os.path.join(dst, srcentry.name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code with a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    copystat(srcname, dstname, follow_symlinks=not symlinks)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occur. copy2 will raise an error
                    if srcentry.is_dir():
                        copytree(srcname, dstname, symlinks, ignore,
                                 copy_function, dirs_exist_ok=dirs_exist_ok)
                    else:
                        copy_function(srcname, dstname)
            elif srcentry.is_dir():
                copytree(srcname, dstname, symlinks, ignore, copy_function,
                         dirs_exist_ok=dirs_exist_ok)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        # Copying file access times may fail on Windows
        if getattr(why, 'winerror', None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)
    return dst

patchname = ""
firmver = ""
titleid = ""
text_end = 0x0
text_padding_end = 0x0
patch = bytearray()

def current_patch_directory():
    return "build/" + firmver + "/" + patchname + "/" + "/luma/" + "/titles/" + titleid

def begin_patch(_titleid, _text_end, _text_padding_end):
    global patch, titleid, text_end, text_padding_end
    patch = str.encode("PATCH")
    titleid = _titleid
    text_end = _text_end
    text_padding_end = _text_padding_end

def end_patch():
    global patch, firmver, patchname, titleid
    patch += str.encode("EOF");
    with suppress(FileExistsError): os.mkdir("build")
    with suppress(FileExistsError): os.mkdir("build/" + firmver)
    with suppress(FileExistsError): os.mkdir("build/" + firmver + "/" + patchname)
    with suppress(FileExistsError): os.mkdir("build/" + firmver + "/" + patchname + "/luma/")
    with suppress(FileExistsError): os.mkdir("build/" + firmver + "/" + patchname + "/luma/" + "/titles/")
    with suppress(FileExistsError): os.mkdir("build/" + firmver + "/" + patchname + "/" + "/luma/" + "/titles/" + titleid)
    open(current_patch_directory() + "/code.ips", "wb").write(patch)

def make_branch_link(src, dst):
    opcode = 0xEB000000 | ((((dst - src) >> 2) - 2) & 0xFFFFFF)
    return struct.pack("<I", opcode)

def make_branch_link_diff(diff):
    opcode = 0xEB000000 | ((((diff) >> 2) - 2) & 0xFFFFFF)
    return struct.pack("<I", opcode)

def add_function_call(addr, inputfile, outputfile, substitutions = {}):
    global patch, text_end, text_padding_end
    if subprocess.call(["armips", inputfile]) != 0:
        exit(1)

    content = bytearray(open(outputfile, "rb").read())
    if text_end + len(content) > text_padding_end:
        print(titleid + ": Not enough free space for function body")
        return

    patch += struct.pack(">I", addr)[1:]
    patch += struct.pack(">H", 0x0004)
    patch += make_branch_link(addr, text_end)

    i = 0
    while i < len(content):
        word = struct.unpack("<I", content[i:i+4])[0]
        if word in substitutions:
            content[i:i+4] = struct.pack("<I", substitutions[word])
        i += 4

    patch += struct.pack(">I", text_end)[1:]
    patch += struct.pack(">H", len(content))
    patch += content

    text_end += len(content)

def make_instruction(instruction):
    source = ".arm.little\n.create \"instruction.bin\",0\n.arm\n_start:\n" + instruction + "\n.close\n"
    open("instruction.s", "w").write(source)
    if subprocess.call(["armips", "instruction.s"]) != 0:
        exit(1)
    out = open("instruction.bin", "rb").read()
    os.remove("instruction.s")
    os.remove("instruction.bin")
    return out

def replace_instruction(addr, instruction):
    global patch
    patch += struct.pack(">I", addr)[1:]
    patch += struct.pack(">H", 0x0004)
    patch += make_instruction(instruction)

def exheader_add_service(exheader, service):
    for i in range(0x250, 0x350, 8):
        if exheader[i:i+8] == bytearray(8):
            exheader[i:i+8] = bytearray(service, "ascii")
            break
    for i in range(0x650, 0x750, 8):
        if exheader[i:i+8] == bytearray(8):
            exheader[i:i+8] = bytearray(service, "ascii")
            break
    return exheader

def exheader_fix_code_size(exheader, codesize):
    u32_bytes = struct.pack('<I', codesize)
    exheader[0x18:0x1C] = u32_bytes
    return exheader

#
# statusbatpercent
#

def patch_statusbatpercent_JP():
    """ Battery percent in statusbar """
    begin_patch("0004003000008202", 0x20514C, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF1F0, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    end_patch()

def patch_statusbatpercent_US():
    """ Battery percent in statusbar """
    begin_patch("0004003000008F02", 0x205174, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF0BC, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    end_patch()

def patch_statusbatpercent_EU():
    """ Battery percent in statusbar """
    begin_patch("0004003000009802", 0x20560C, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF3A8, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    end_patch()

#
# statusbaticon
#

def patch_statusbaticon_JP():
    """ Battery icon in statusbar shows each bar as 25% of charge """
    begin_patch("0004003000008202", 0x20514C, 0x206000)
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF3CC, "src/statusbatteryicon.s", "statusbatteryicon.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412E9
    })
    end_patch()

def patch_statusbaticon_US():
    """ Battery icon in statusbar shows each bar as 25% of charge """
    begin_patch("0004003000008F02", 0x205174, 0x206000)
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF298, "src/statusbatteryicon.s", "statusbatteryicon.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412E9
    })
    end_patch()

def patch_statusbaticon_EU():
    """ Battery icon in statusbar shows each bar as 25% of charge """
    begin_patch("0004003000009802", 0x20560C, 0x206000)
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF584, "src/statusbatteryicon.s", "statusbatteryicon.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412E9
    })
    end_patch()

#
# statusbatpercent + statusbaticon
#

def patch_both_JP():
    """ Battery percent in statusbar """
    begin_patch("0004003000008202", 0x20514C, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF1F0, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF3CC, "src/statusbatteryiconalt.s", "statusbatteryiconalt.bin", {
        0xdead0001 : 0x3412E9,
        0xe1a00000 : struct.unpack("<I", make_branch_link_diff(-280))[0]
    })
    end_patch()

def patch_both_US():
    """ Battery percent in statusbar """
    begin_patch("0004003000008F02", 0x205174, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF0BC, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF298, "src/statusbatteryiconalt.s", "statusbatteryiconalt.bin", {
        0xdead0001 : 0x3412E9,
        0xe1a00000 : struct.unpack("<I", make_branch_link_diff(-280))[0]
    })
    end_patch()

def patch_both_EU():
    """ Battery percent in statusbar """
    begin_patch("0004003000009802", 0x20560C, 0x206000)
    # Append battery percent to minute string
    add_function_call(0x000EF3A8, "src/statusbattery.s", "statusbattery.bin", {
        0xdead0000 : 0x33C14C,
        0xdead0001 : 0x3412D9
    })
    # Replace call to GetBatteryLevel
    add_function_call(0x000EF584, "src/statusbatteryiconalt.s", "statusbatteryiconalt.bin", {
        0xdead0001 : 0x3412E9,
        0xe1a00000 : struct.unpack("<I", make_branch_link_diff(-280))[0]
    })
    end_patch()

#
# sm_home
#

def patch_sm_home_J():
    exheader = bytearray(open("extheader_J.bin", "rb").read())
    exheader_patched = exheader_add_service(exheader, "mcu::HWC")
    exheader_fixed = exheader_fix_code_size(exheader_patched, 0x206000)
    open(current_patch_directory() + "/exheader.bin", "wb").write(exheader_fixed)
    if patchname != "statusbaticon":
        copytree('romfs', os.path.join(current_patch_directory(), 'romfs'), dirs_exist_ok=True)

def patch_sm_home_U():
    exheader = bytearray(open("extheader_U.bin", "rb").read())
    exheader_patched = exheader_add_service(exheader, "mcu::HWC")
    exheader_fixed = exheader_fix_code_size(exheader_patched, 0x206000)
    open(current_patch_directory() + "/exheader.bin", "wb").write(exheader_fixed)
    if patchname != "statusbaticon":
        copytree('romfs', os.path.join(current_patch_directory(), 'romfs'), dirs_exist_ok=True)

def patch_sm_home_E():
    exheader = bytearray(open("extheader_E.bin", "rb").read())
    exheader_patched = exheader_add_service(exheader, "mcu::HWC")
    exheader_fixed = exheader_fix_code_size(exheader_patched, 0x206000)
    open(current_patch_directory() + "/exheader.bin", "wb").write(exheader_fixed)
    if patchname != "statusbaticon":
        copytree('romfs', os.path.join(current_patch_directory(), 'romfs'), dirs_exist_ok=True)

### JPN ###
firmver = "11.17.0-50J"
### Create statusbatpercent patches ###
patchname = "statusbatpercent"
patch_statusbatpercent_JP()
patch_sm_home_J()
### Create statusbaticon patches ###
patchname = "statusbaticon"
patch_statusbaticon_JP()
patch_sm_home_J()
### Create statusbatpercent+statusbaticon patches ###
patchname = "both"
patch_both_JP()
patch_sm_home_J()

### US ###
firmver = "11.17.0-50U"
### Create statusbatpercent patches ###
patchname = "statusbatpercent"
patch_statusbatpercent_US()
patch_sm_home_U()
### Create statusbaticon patches ###
patchname = "statusbaticon"
patch_statusbaticon_US()
patch_sm_home_U()
### Create statusbatpercent+statusbaticon patches ###
patchname = "both"
patch_both_US()
patch_sm_home_U()

### EUR ###
firmver = "11.17.0-50E"
### Create statusbatpercent patches ###
patchname = "statusbatpercent"
patch_statusbatpercent_EU()
patch_sm_home_E()
### Create statusbaticon patches ###
patchname = "statusbaticon"
patch_statusbaticon_EU()
patch_sm_home_E()
### Create statusbatpercent+statusbaticon patches ###
patchname = "both"
patch_both_EU()
patch_sm_home_E()

os.remove("statusbattery.bin")
os.remove("statusbatteryicon.bin")
os.remove("statusbatteryiconalt.bin")
