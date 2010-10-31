
import pickle
import os, re, md5
import errno
import shutil
from os.path import join
from os.path import isdir, isfile, dirname, basename, normpath, splitext

from PIL import Image
from urllib import pathname2url as p2u

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse,  HttpResponseForbidden
from django.template import Context
from django.template.loader import render_to_string

# STORAGE_ROOT is relative to MEDIA_ROOT
try:
    STORAGE_ROOT = settings.STORAGE_ROOT
except AttributeError:
    STORAGE_ROOT = os.path.join('images', 'uploads')

# STORAGE_URL is abs url to root folder of the storage
try:
    STORAGE_URL = settings.STORAGE_URL
except AttributeError:
    STORAGE_URL = os.path.join(settings.MEDIA_URL, STORAGE_ROOT)

FULL_STORAGE_URL = join(settings.MEDIA_ROOT, STORAGE_ROOT)

THUMBS_SUBDIR = '.thumbs'

r = '\d{3}x\d{3}'
THUMB_PATTERN = re.compile(r)
    
ALLOWED_IMAGES = ('jpeg','jpg','gif','png')

class Thumbs:
    def __init__(self, path):
        self.top = path
        if path:
            self.dbfile = join(FULL_STORAGE_ROOT, path, THUMBS_SUBDIR, '.db')
        else:
            self.dbfile = join(FULL_STORAGE_ROOT, THUMBS_SUBDIR, '.db')

    def load(self):
        files = {}
        if isfile(self.dbfile):
            input = open(self.dbfile, 'rb')
            try:
                files = pickle.load(input)
            finally:
                input.close()
        return files
        
    def dump(self, files):
        output = open(self.dbfile, 'wb')
        try:
            pickle.dump(files, output)
        finally:
            output.close()

@staff_member_required
def show_tree(request, type, path):
    #return HttpResponse(DirStructure('files', 'first', $this->AccessDir($_POST['path'], 'files'))
    if path:
        path = path.strip('/')    
    return HttpResponse(dir_structure(type, path))

@staff_member_required
def show_path(request, type, path):
    if path:
        path = path.strip('/')    

    return HttpResponse(dir_path(type, path))

@staff_member_required
def show_dir(request, type, path):
    if path:
        path = path.strip('/')    
    
    return HttpResponse(dir_show(type, path))

@staff_member_required
def new_folder(request, path, name):
    error = ''
    try:
        os.mkdir(join(FULL_STORAGE_ROOT, path, name))
    except Exception, e:
        error = e
    tree = dir_structure('images', '', join(path, name)).replace('\n', '')
    path = dir_path('images', join(path, name)).replace('\n', '')
    
    return HttpResponse("{'tree':'%s', 'addr':'%s', 'error':'%s'}" % (tree, path, error))

@staff_member_required
def del_folder(request, path):
    rmdir_r(join(FULL_STORAGE_ROOT, path))
    return HttpResponse("{ok:''}");

def rmdir_r(top):
    shutil.rmtree(top, ignore_errors=True)

def walktree(top=".", depthfirst=True):
    import stat, types
    names = os.listdir(top)
    if not depthfirst:
        yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            for (newtop, children) in walktree(os.path.join(top, name), depthfirst):
                yield newtop, children
    if depthfirst:
        yield top, names
    
def dir_path(type, path=""):
    
    class PathItem(object ):
        def __init__(self, path, add_path):
            self.path = path
            self.add_path = add_path 
    openfn = 'folder_open_image'
    if type != "images":
        openfn = 'folder_open_document'

    path = normpath(path).split('/')
    res_path = []
    add_path = '/'
    for p in path:
        add_path = join(add_path,p)
        res_path.append(PathItem(p, add_path)) 
        
    context = Context(
                      {'openfn' : 'img/%s.png' % openfn,
                       'type' : type,
                       'res_path':res_path
                       })
    return render_to_string('path.html', context_instance = context)

def dir_structure(type, top='', current_dir='', level=0):
    if top == '/':
        top = ''
    from xml.sax.saxutils import escape # To quote out things like &amp;
    #import os, stat, types
    
    top_name = basename(dirname(top))
    folder_class = 'folderS'
    folder_opened = ''
    class_act = ''
    if top == current_dir:
        class_act = 'folderAct'
    elif re.compile('^'+top).search(current_dir):
        folder_class = 'folderOpened'
        folder_opened = 'style="display:block;"'
    ret = ''
    type_name = 'Files'
    if type == 'images':
        type_name = 'Images'

    # firstly read inner directories
    files_num = 0
    dirs_num = 0
    inner = ""
    fdir = join(FULL_STORAGE_ROOT, top)
    for name in os.listdir(fdir):
        if isdir(join(fdir, name)) and not name.startswith('.'):
            inner += dir_structure(type, os.path.join(top, name), current_dir, level+1)
            dirs_num += 1
        elif isfile(join(fdir, name)) and not THUMB_PATTERN.search(name):
            files_num += 1
    # save current (top) directory
    if top == '':
        ret += '<div class="folder%s %s" path="" pathtype="%s">%s (%d)</div>\n' % (type.capitalize(), class_act, type, type_name, files_num)
        if inner != "":

            ret += '<div class="folderOpenSection" style="display:block;">\n' + inner + '</div>\n'
    else:
        if inner != "":
            ret += '  <div class="%s %s" path="%s" title="Files: %d,Directories: %d" pathtype="%s">%s (%d)</div>\n' % (folder_class, class_act, escape(top), files_num, dirs_num, type, escape(basename(top)), files_num)
            ret += '  <div class="folderOpenSection" ' + folder_opened + '>\n' + inner + '  </div>\n'
        else:
            ret += '  <div class="folderClosed %s" path="%s" title="" pathtype="%s">%s (%d)</div>\n' % (class_act, escape(top), type, escape(basename(top)), files_num)
    
    return ret

def dir_show(type, top):

    fdir = join(FULL_STORAGE_ROOT, top)
    files = Thumbs(top).load()
    
    class FileInfo(object):
        def __init__(self, f_name, ext, linkto, fsize, fdate, fwidth, fheight, md5_digest, url, abs_url):
            self.f_name = f_name
            self.ext = ext
            self.linkto = linkto
            self.fsize = fsize
            self.fdate = fdate
            self.fwidth = fwidth
            self.fheight = fheight
            self.md5_digest = md5_digest
            self.url = url
            self.abs_url = abs_url

    objects = []

    for f_name in os.listdir(fdir):
        if os.path.isfile(join(fdir, f_name)):
            if files.has_key(f_name):
                info = files[f_name]
                ext = info['ext'].upper()
                linkto = join(top,f_name)
                fsize = info['size']
                fdate = info['date']
                fwidth = info['width']
                fheight = info['height']
                md5_digest = info['md5']
            else:
                fullname = join(fdir, f_name)
                f = open(fullname, 'rb')
                try:
                    img = Image.open(f)
                    md5_digest = md5.new(f.read()).hexdigest()
                except: #not a valid image. skiping...
                    continue
                finally:
                    f.close()
                name_, ext = splitext(f_name)
                ext = ext.upper()
                linkto = fullname
                fsize = os.path.getsize(fullname)
                fdate = os.path.getmtime(fullname)
                fwidth, fheight = img.size
            url = p2u(join(top,f_name)) # XXX join url with path
            abs_url = p2u(os.path.join(STORAGE_ROOT, url))

            objects.append(FileInfo(f_name, ext, linkto, fsize, fdate, fwidth, fheight, md5_digest, url, abs_url))
    
    context = Context({'objects':objects,
                      })
    
    return render_to_string('show_dir.html', context_instance=context)

@staff_member_required
def del_file(request):
    path = request.POST['path'].strip('/')

    files = Thumbs(path).load()

    for filename in request.POST.getlist('filename'):
        if files.has_key(filename):
            del files[filename]

        fullpath = os.path.join(FULL_STORAGE_ROOT, path, filename)
        try:
            os.remove(fullpath)
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise
    
    Thumbs(path).dump(files)
    return HttpResponse(show_dir(request, path))

@staff_member_required
def upload_file(request):
    try:
        path = request.POST.get('path')
        path = path.strip('/')
        top = path
        if not isdir(join(FULL_STORAGE_ROOT, top, THUMBS_SUBDIR)):
            os.mkdir(join(FULL_STORAGE_ROOT, top, THUMBS_SUBDIR))
        
        files = Thumbs(top).load()
        
        if (len(request.FILES)):
            for file in request.FILES.items():
                if -1 == file[1].name.rfind('.'):
                    return HttpResponseForbidden()
                
                (name, ext) = file[1].name.rsplit('.', 2)
                if not ext.lower() in ALLOWED_IMAGES:
                    return HttpResponseForbidden()
                
                file_body = file[1].read()
                md5_digest = md5.new(file_body).hexdigest()
                
                filename = name + '.' + ext
                filelink = join(top,filename)
                filepath = join(FULL_STORAGE_ROOT, top, filename)
                
                img_file = open(filepath, 'wb')
                try:
                    img_file.write(file_body)
                finally:
                    img_file.close()
                
                img_file = open(filepath, 'rb')
                try:
                    image = Image.open(img_file)
                finally:
                    img_file.close()

                xsize, ysize = image.size
                
                files[filename] = {
                    'filename': filename,
                    'name':     name,
                    'ext':      ext,
                    'path':     top,
                    'link':     filelink,
                    'size':     file[1].size,
                    'date':     os.path.getmtime(filepath),
                    'width':    xsize,
                    'height':   ysize,
                    'md5':      md5_digest
                }
                
        Thumbs(top).dump(files)
    except Exception, e:
        import traceback
        traceback.print_exc()
        raise
    return HttpResponse('Ok.')

@staff_member_required
def sid(request):
    return HttpResponse(request.COOKIES.get('sessionid'))