SUMMARY = "Adds the pi user"
SECTION = "conf"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
PR = "r0"

SRCREV_dotfiles = "fa97e077944d36e320201a2627cc6a75e4f1bceb"
SRCREV_vundle = "5548a1a937d4e72606520c7484cd384e6c76b565"
SRCREV_maktaba = "fe95bb10f6bb250943a44632107f6a3d76ce5f28"
SRCREV_codefmt = "ff464a478202df40ae484e6e94a1d56587fcc69e"
SRCREV_glaive = "3c5db8d279f86355914200119e8727a085863fcd"
SRCREV_FORMAT = "dotfiles_vundle_maktaba_codefmt_glaive"

SRC_URI = "file://home/pi/.ssh/authorized_keys \
           file://etc/security/limits.d/rt.conf \
           git://github.com/AustinSchuh/.dotfiles.git;protocol=https;branch=main;name=dotfiles \
           git://github.com/VundleVim/Vundle.vim.git;protocol=https;branch=master;name=vundle;destsuffix=vundle \
           git://github.com/google/vim-maktaba.git;protocol=https;branch=master;name=maktaba;destsuffix=maktaba \
           git://github.com/google/vim-codefmt.git;protocol=https;branch=master;name=codefmt;destsuffix=codefmt \
           git://github.com/google/vim-glaive.git;protocol=https;branch=master;name=glaive;destsuffix=glaive \
           "

PACKAGES =+ "${PN}-pi"

S = "${UNPACKDIR}"

inherit useradd

GROUPADD_PARAM:${PN} = "sudo; video; system-journal; dialout; adm"

USERADD_PACKAGES = "${PN}"

# user: pi, password: raspberry
USERADD_PARAM:${PN} = "-G sudo,video,system-journal,dialout,adm -m -p \"\\\$y\\\$j9T\\\$85lzhdky63CTj.two7Zj20\\\$pVY53UR0VebErMlm8peyrEjmxeiRw/rfXfx..9.xet1\" -r -s /bin/bash pi"


install_content() {
    set -x
    install -D -m"$1" "$2" "${D}${base_prefix}/$2"
    chown "$3" "${D}${base_prefix}/$2"
}

install_vim_plugins() {
    vim_home="$1"
    install -d -m0755 "${vim_home}/.vim/bundle"
    rsync --recursive --exclude '.git' ${UNPACKDIR}/vundle/ "${vim_home}/.vim/bundle/Vundle.vim/"
    rsync --recursive --exclude '.git' ${UNPACKDIR}/maktaba/ "${vim_home}/.vim/bundle/vim-maktaba/"
    rsync --recursive --exclude '.git' ${UNPACKDIR}/codefmt/ "${vim_home}/.vim/bundle/vim-codefmt/"
    rsync --recursive --exclude '.git' ${UNPACKDIR}/glaive/ "${vim_home}/.vim/bundle/vim-glaive/"
}

do_install() {
    set -x
    mkdir -p -m755 ${D}${base_prefix}/home/pi/.ssh
    mkdir -p -m755 ${D}${base_prefix}/home/pi/bin/logs

    install -D -m0600 home/pi/.ssh/authorized_keys ${D}${base_prefix}/home/pi/.ssh/authorized_keys
    chown pi:pi ${D}${base_prefix}/home/pi/.ssh/authorized_keys

    # Install dotfiles.
    mkdir -p ${D}${base_prefix}/home/pi/.dotfiles
    rsync --recursive --verbose --exclude '.git' ${UNPACKDIR}/${BB_GIT_DEFAULT_DESTSUFFIX}/ ${D}${base_prefix}/home/pi/
    chown -R pi:pi ${D}${base_prefix}/home/pi/

    # Now setup vundle for vim.
    install_vim_plugins ${D}${base_prefix}/home/pi
    chown -R pi:pi ${D}${base_prefix}/home/pi/

    # Do it for root too...
    mkdir -p ${D}${base_prefix}${ROOT_HOME}/.dotfiles
    rsync --recursive --verbose --exclude '.git' ${UNPACKDIR}/${BB_GIT_DEFAULT_DESTSUFFIX}/ ${D}${base_prefix}${ROOT_HOME}/
    chown -R root:root ${D}${base_prefix}${ROOT_HOME}/
    install_vim_plugins ${D}${base_prefix}${ROOT_HOME}
    chown -R root:root ${D}${base_prefix}${ROOT_HOME}


    mkdir -p ${D}${sysconfdir}/sudoers.d/

    echo "pi ALL=(ALL) NOPASSWD: ALL" > ${D}${sysconfdir}/sudoers.d/001_pi

    install_content 0644 "etc/security/limits.d/rt.conf" "root:root"

    mkdir -p -m755 ${D}${base_prefix}/etc/bash_completion.d/
    ln -s /usr/share/bash-completion/completions/git-prompt.sh ${D}${base_prefix}/etc/bash_completion.d/git-prompt
    chown -h root:root ${D}${base_prefix}/etc/bash_completion.d/git-prompt
}

RDEPENDS:${PN} += " git bash vim git-bash-completion perl"
DEPENDS += " git bash vim rsync-native"

FILES:${PN} = "${base_prefix}/home/pi"
FILES:${PN}:append = " ${base_prefix}${ROOT_HOME}"
FILES:${PN}:append = " ${base_prefix}/etc/sudoers.d/001_pi"
FILES:${PN}:append = " ${base_prefix}/etc/security/limits.d/rt.conf"
FILES:${PN}:append = " ${base_prefix}/etc/bash_completion.d/git-prompt"
