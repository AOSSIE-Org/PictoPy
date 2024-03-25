block_cipher = None


a = Analysis(['Image_Classifier.py'],
             pathex=['C:\\Users\\hp\\Desktop\\Tkinter ML'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

a.datas += [('\\dist\\Class.ico','C:\\Users\\hp\\Desktop\\Tkinter ML\\Class.ico', "DATA"), ('\\astor\\VERSION','C:\\Users\\hp\\Desktop\\Tkinter ML\\VERSION', "DATA")]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Image Classifier',
          debug=False,
          strip=False,
          upx=True,
          console=False,
		  icon='C:\\Users\\hp\\Desktop\\Tkinter ML\\Class.ico')