yum-lag
=======

Yum plugin to allow excluding updates newer than a given period. Intended to
allow simple update staging

## Installation

To manually install, put `lag.py` in `/usr/lib/yum-plugins/` and put `lag.conf`
in `/etc/yum/pluginconf.d/`.

## Configuration

Configuration options are explained in `lag.conf`. You can also use the
*exclude_newer_than* option in the repo config sections to override the global
value.

## Usage

Nothing special needs to be done to use the plugin, though note that it only
applies to the *update* and *upgrade* YUM commands and is bypassed for *install*
and etc. The plugin also adds a `--exclude-newer-than` option to override both
the global and per-repo *exclude_newer_than* options.

## Examples

~~~~
$ sudo yum update
Loaded plugins: fastestmirror, lag
Loading mirror speeds from cached hostfile
 * fedora: mirror.steadfast.net
 * rpmfusion-free: mirror.nexcess.net
 * rpmfusion-free-updates: mirror.nexcess.net
 * rpmfusion-nonfree: mirror.nexcess.net
 * rpmfusion-nonfree-updates: mirror.nexcess.net
 * updates: mirror.steadfast.net
Resolving Dependencies
--> Running transaction check
---> Package libsmbclient.x86_64 2:4.0.4-3.fc18 will be updated
---> Package libsmbclient.x86_64 2:4.0.5-1.fc18 will be an update
---> Package libwbclient.x86_64 2:4.0.4-3.fc18 will be updated
---> Package libwbclient.x86_64 2:4.0.5-1.fc18 will be an update
---> Package perl-DBD-MySQL.x86_64 0:4.022-1.fc18 will be updated
---> Package perl-DBD-MySQL.x86_64 0:4.023-1.fc18 will be an update
---> Package samba-client.x86_64 2:4.0.4-3.fc18 will be updated
---> Package samba-client.x86_64 2:4.0.5-1.fc18 will be an update
---> Package samba-common.x86_64 2:4.0.4-3.fc18 will be updated
---> Package samba-common.x86_64 2:4.0.5-1.fc18 will be an update
---> Package samba-libs.x86_64 2:4.0.4-3.fc18 will be updated
---> Package samba-libs.x86_64 2:4.0.5-1.fc18 will be an update
---> Package samba-winbind.x86_64 2:4.0.4-3.fc18 will be updated
---> Package samba-winbind.x86_64 2:4.0.5-1.fc18 will be an update
---> Package samba-winbind-clients.x86_64 2:4.0.4-3.fc18 will be updated
---> Package samba-winbind-clients.x86_64 2:4.0.5-1.fc18 will be an update
--> Finished Dependency Resolution

Dependencies Resolved

=================================================================================================================
 Package                            Arch                Version                       Repository            Size
=================================================================================================================
Updating:
 libsmbclient                       x86_64              2:4.0.5-1.fc18                updates              109 k
 libwbclient                        x86_64              2:4.0.5-1.fc18                updates               77 k
 perl-DBD-MySQL                     x86_64              4.023-1.fc18                  updates              139 k
 samba-client                       x86_64              2:4.0.5-1.fc18                updates              444 k
 samba-common                       x86_64              2:4.0.5-1.fc18                updates              688 k
 samba-libs                         x86_64              2:4.0.5-1.fc18                updates              4.1 M
 samba-winbind                      x86_64              2:4.0.5-1.fc18                updates              432 k
 samba-winbind-clients              x86_64              2:4.0.5-1.fc18                updates              140 k

Transaction Summary
=================================================================================================================
Upgrade  8 Packages

Total download size: 6.1 M
Is this ok [y/N]: n
~~~~

~~~~
$ sudo yum update --exclude-newer-than 30
Loaded plugins: fastestmirror, lag
Loading mirror speeds from cached hostfile
 * fedora: mirror.steadfast.net
 * rpmfusion-free: mirror.nexcess.net
 * rpmfusion-free-updates: mirror.nexcess.net
 * rpmfusion-nonfree: mirror.nexcess.net
 * rpmfusion-nonfree-updates: mirror.nexcess.net
 * updates: mirror.steadfast.net
No Packages marked for Update
~~~~
