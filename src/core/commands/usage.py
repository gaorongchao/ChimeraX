# vim: set expandtab shiftwidth=4 softtabstop=4:


def usage(session, command_name=None):
    '''Display command usage.

    Parameters
    ----------
    command_name : string
        Show documentation for the specified command.  If no command is specified
        then the names of all commands are shown.  If the command name "all" is
        given then a synopsis for each command is shown.  The command name can
        be abbreviated.
    '''
    from . import cli
    status = session.logger.status
    info = session.logger.info
    if command_name is None:
        info("Use 'usage <command>' for a command synopsis.")
        info("Use 'help <command>' to learn more about a command.")
        cmds = cli.registered_commands(multiword=True)
        if len(cmds) > 0:
            text = cli.commas(cmds, ' and')
            noun = cli.plural_form(cmds, 'command')
            verb = cli.plural_form(cmds, 'is', 'are')
            info("The following %s %s available: %s" % (noun, verb, text))
        return
    elif command_name == 'all':
        info("Syntax for all commands:")
        cmds = cli.registered_commands(multiword=True)
        if not session.ui.is_gui:
            for name in cmds:
                try:
                    info(cli.usage(name, no_subcommands=True))
                except:
                    info('%s -- no documentation' % name)
            return
        for name in cmds:
            try:
                info(cli.html_usage(name, no_subcommands=True), is_html=True)
            except:
                from html import escape
                info('<b>%s</b> &mdash; no documentation' % escape(name),
                     is_html=True)
        return

    try:
        usage = cli.usage(command_name)
    except ValueError as e:
        status(str(e))
        return
    if session.ui.is_gui:
        info(cli.html_usage(command_name), is_html=True)
    else:
        info(usage)


def register_command(session):
    from . import cli
    desc = cli.CmdDesc(optional=[('command_name', cli.RestOfLine)],
                       non_keyword=['command_name'],
                       synopsis='show command usage')
    cli.register('usage', desc, usage)
