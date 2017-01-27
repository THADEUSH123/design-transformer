"""Manipulate deployment data.

Import/Export feature properties in misc formats.
"""

import datastore
import os
import reports


def get_user_general_choice(prompt, default_choice, valid_options):
    """Prompt user to select a general menu option."""
    print('d11111')
    while True:
        choice = raw_input(prompt.format(default_choice)) or default_choice
        if choice in valid_options:
            return choice
        else:
            print('   Invalid selection.')


import_valid_options = ['1', '2', '3']
import_prompt = ('\n============IMPORT MENU================='
                 '\nLoad multiple data sets in the following ways:'
                 '\n1 => Import multiple files from a folder'
                 '\n2 => Import one specific file'
                 '\n3 => Do not load additional files'
                 '\nEnter menu choice[{}]: ')

export_valid_options = ['1', '2', '3']
export_prompt = ('\n============EXPORT MENU================='
                 '\nSave current data set to multiple locations/formats:'
                 '\n1 => Export data to a folder'
                 '\n2 => Change destination folder'
                 '\n3 => Do not save in additional formats/locations'
                 '\nEnter choice[{}]: ')


main_valid_options = ['1', '2', '3']
main_prompt = ('\n============MAIN MENU================='
               '\nSelect an action to perform:'
               '\n1 => Load data.'
               '\n2 => Export data.'
               '\n3 => Exit'
               '\nEnter choice[{}]: ')


def import_menu(datastore, folder, file_path=None, choice='1'):
    """Import data based on user supplied input."""

    def get_user_file_choices(files):
        """Prompt user for which files consume."""
        files = filter(lambda x: x.endswith(
                      ('.gv', '.csv', '.json', '.geojson')), files)
        for f in list(files):
            while True:
                decision = raw_input('Import {}?[Y/n]'.format(f)) or 'y'
                if decision.lower() not in ['y', 'n']:
                    print('   Invalid selection')
                    continue
                elif decision.lower() == 'y':
                    print('   Adding file to import list')
                    break
                elif decision.lower() == 'n':
                    print('   Removing file from import list')
                    files.remove(f)
                    break
        return files

    while True:
        choice = get_user_general_choice(prompt=import_prompt,
                                         default_choice=choice,
                                         valid_options=import_valid_options)
        if choice is '1':
            folder_prompt = 'Enter folder to import[{}]: '.format(folder)
            folder = raw_input(folder_prompt) or folder
            files_names = get_user_file_choices(os.listdir(folder))
            datastore.import_all_files(folder, files_names)
        elif choice is '2':
            file_prompt = 'Enter file name[{}]: '.format(file_path)
            file_path = raw_input(file_prompt) or file_path
            datastore.import_files(os.path.dirname(file_path),
                                   [os.path.basename(file_path)])

        elif choice is '3':
            break

        choice = '3'


def export_menu(datastore, folder='exports', choice='1'):
    """Export data based on user supplied input."""

    while True:
        choice = get_user_general_choice(prompt=export_prompt,
                                         default_choice=choice,
                                         valid_options=export_valid_options)
        if choice is '1':
            datastore.update_all_properties()
            reports.export_all_files(to_folder=folder,
                                     sites=datastore.sites,
                                     links=datastore.links)
            choice = '3'

        if choice is '2':
            folder_prompt = 'Enter folder name[{}]: '.format(folder)
            folder = raw_input(folder_prompt) or folder
            choice = '1'

        if choice is '3':
            break

        choice = '3'


def main():
    """Main function for direct execution."""
    choice = '1'
    ds = datastore.Datastore()
    while True:
        choice = get_user_general_choice(prompt=main_prompt,
                                         default_choice=choice,
                                         valid_options=main_valid_options)

        if choice is '1':
            import_menu(datastore=ds, folder=os.getcwd())
            choice = '2'

        elif choice is '2':
            export_menu(datastore=ds)
            choice = '3'

        elif choice is '3':
            exit()

        else:
            print('Invalid choice')

        print('\n' * 2)


if __name__ == '__main__':
    main()
