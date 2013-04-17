
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template import RequestContext
from django.conf import settings
import urllib, urlparse, datetime, os, re, md5
from os.path import isdir, isfile, dirname, basename
try:
    from PIL import Image
except ImportError:
    import Image
#from pickle import Pickler, Unpickler
import pickle

STORAGE_ROOT = 'uploads/'
ALLOWED_IMAGES = ('jpeg','jpg','gif','png')
ALLOWED_FILES = ('doc','docx','ppt','pptx','xls','xlsx','mdb','accdb', 'swf', 'zip', 'rar', 'rtf', 'pdf', 'psd', 'mp3', 'wma')

class Thumbs:
    def __init__(self, path):
        self.top = path.strip('/') + '/'
        self.dbfile = STORAGE_ROOT + self.top + '.thumbs/.db'
    
    def load(self):
        files = {}
        if isfile(self.dbfile):
            input = open(self.dbfile, 'rb')
            files = pickle.load(input)
            input.close()
        return files
        
    def dump(self, files):
        output = open(self.dbfile, 'wb')
        pickle.dump(files, output)
        output.close()
    
def all(request):
    #print "all"
    #if request.POST.has_key('SID'):
    #    print "sessionid(%s) == SID(%s)" % (request.COOKIES.get('sessionid'), request.POST['SID'])
    #print request.POST
    if not request.user.is_staff and request.COOKIES.get('sessionid') != request.POST['SID']:
        raise Http404

    act = request.POST['action']
    if act == "showpath":
        return showpath(request)
    elif act == "showtree":
        return showtree(request)
    elif act == "showdir":
        return showdir(request)
    elif act == 'newfolder':
        return newfolder(request)
    elif act == 'delfolder':
        return delfolder(request)
    elif act == 'uploadfile':
        return uploadfile(request)
    elif act == 'delfile':
        return delfile(request)
    elif act == 'SID':
        return HttpResponse(request.COOKIES.get('sessionid'))
    
    return HttpResponseForbidden("oh-la-la")
    #files = FileUpload.objects.all().order_by('-upload_date')
    #return render_to_response('upload/base.html', {'files': files, 'textarea_id': request.GET['textarea']}, context_instance=RequestContext(request))

def showpath(request):
    return HttpResponse(DirPath(request.POST['type'], request.POST['path']))

def showtree(request):
    #return HttpResponse(DirStructure('files', 'first', $this->AccessDir($_POST['path'], 'files'))
    path = request.POST.get('path', '')
    return HttpResponse(DirStructure('images', '/', path))

def showdir(request):
    return HttpResponse(ShowDir(request.POST['path']))
    
def newfolder(request):
    name = request.POST['name']
    top = request.POST['path']
    top = top.lstrip('/');
    os.mkdir(STORAGE_ROOT + top + name)
    
    tree = DirStructure('images', '/', top + name).replace('\n', '')
    path = DirPath('images', top + name).replace('\n', '')
    error = ''
    return HttpResponse("{'tree':'%s', 'addr':'%s', 'error':'%s'}" % (tree, path, error))

def delfolder(request):
    path = request.POST['path'].lstrip('/')
    #print 'rmdir ' + STORAGE_ROOT + path
    rmdir_r(STORAGE_ROOT + path)
    return HttpResponse("{ok:''}");

def uploadfile(request):
    return UploadFile(request)

def delfile(request):
    top = request.POST['path'].strip('/') + '/'
    files = Thumbs(top).load()
    
    for key in request.POST:
        if re.search('^filename', key):
            fname = request.POST[key]
            if files.has_key(fname): del files[fname]
            os.remove(STORAGE_ROOT + top + fname)
    
    Thumbs(top).dump(files)
    return HttpResponse(ShowDir(request.POST['path']))

def download(request):
    '''Saves image from URL and returns ID for use with AJAX script'''
    if not request.user.is_staff:
        raise Http404
    if request.method == 'GET':
        f = FileUpload();
        f.title = request.GET['title'] or 'untitled'
        f.description = request.GET['description']
        url = urllib.unquote(request.GET['photo'])
        file_content = urllib.urlopen(url).read()
        file_name = url.split('/')[-1]
        f.save_upload_file(file_name, file_content)
        f.save()
        return HttpResponse('%s' % (f.id))
    else:
        raise Http404


def rmdir_r(top):
    for f in walktree(top):
        path = f[0]
        if os.path.isfile(path): os.remove(path)
        elif os.path.isdir(path): os.rmdir(path)

# recusive directory walking
def walktree(top = ".", depthfirst = True):
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
            for (newtop, children) in walktree (os.path.join(top, name), depthfirst):
                yield newtop, children
    if depthfirst:
        yield top, names

# recursive function
def DirStructure(type, top='', currentDir='', level=0):
    from xml.sax.saxutils import escape # To quote out things like &amp;
    #import os, stat, types
    
    if top == '': top = '/'
    if currentDir == '': currentDir = '/'
    topName = basename(dirname(top))
    folderClass = 'folderS'
    folderOpened = ''
    classAct = ''
    if top.strip('/') == currentDir.strip('/'): classAct = 'folderAct'
    elif re.compile('^'+top.strip('/')).search(currentDir.strip('/')):
        folderClass = 'folderOpened'
        folderOpened = 'style="display:block;"'
    ret = ''
    typeName = 'Files'
    if type == 'images': typeName = 'Images'

    # firstly read inner directories
    files_num = 0
    dirs_num = 0
    inner = ""
    for name in os.listdir(STORAGE_ROOT + top):
        if isdir(STORAGE_ROOT + top + name) and not name.startswith('.'):
            inner += DirStructure(type, top + name + '/', currentDir, level+1)
            dirs_num += 1
        elif isfile(STORAGE_ROOT + top + name):
            files_num += 1
    
    # save current (top) directory
    if top == '/':
        ret += '<div class="folder%s %s" path="/" pathtype="%s">%s (%d)</div>\n' % (type.capitalize(), classAct, type, typeName, files_num)
        if inner != "":
            ret += '<div class="folderOpenSection" style="display:block;">\n' + inner + '</div>\n'
    else:
        if inner != "":
            ret += '  <div class="%s %s" path="%s" title="Files: %d,Directories: %d" pathtype="%s">%s (%d)</div>\n' % (folderClass, classAct, escape(top), files_num, dirs_num, type, escape(basename(topName)), files_num)
            ret += '  <div class="folderOpenSection" ' + folderOpened + '>\n' + inner + '  </div>\n'
        else:
            ret += '  <div class="folderClosed %s" path="%s" title="" pathtype="%s">%s (%d)</div>\n' % (classAct, escape(top), type, escape(basename(topName)), files_num)
    
    return ret

def DirPath(type, path=""):
    import re
    path = path.strip('/')
    if path != "":
        path = re.split('[\\/]', path)
    
    openfn = 'folder_open_image'
    if type != "images": openfn = 'folder_open_document'
    ret = """
    <div class="addrItem" path="" pathtype="%s" title="">
        <img src="img/%s.png" width="16" height="16" alt="Root Directory" />
    </div>
    """ % (type, openfn)
    
    i=0;
    addPath = ""
    for v in path:
        i += 1;
        addPath += '/' + v;
        cclass = "addrItem"
        if len(path) == i: cclass = "addrItemEnd"
        ret += '<div class="%s" path="%s" pathtype="%s" title=""><div>%s</div></div>\n' % (cclass, addPath, type, v)
    
    return ret

def ShowDir(top):
    if top == '/': top = ''
    fdir = STORAGE_ROOT + top
    
    files = Thumbs(top).load()
    
    #print "listing files from %s" % (STORAGE_ROOT + top)
    ret = ""
    for file in os.listdir(STORAGE_ROOT + top):
        if os.path.isfile(STORAGE_ROOT + top + file):
            if files.has_key(file):
                info = files[file]
                ext = info['ext'].upper()
                linkto = '/' + fdir + info['link']
                fsize = info['size']
                fdate = info['date']
                fwidth = info['width']
                fheight = info['height']
                md5_digest = info['md5']
            else:
                f = open(fdir + file, 'rb')
                img = Image.open(f)
                name_, ext = file.rsplit('.', 2)
                ext = ext.upper()
                linkto = '/' + fdir + file
                fsize = os.path.getsize(fdir + file)
                fdate = os.path.getmtime(fdir + file)
                fwidth, fheight = img.size
                md5_digest = md5.new(f.read()).hexdigest()
                f.close()
            ret += """
    <table class="imageBlock0" cellpadding="0" cellspacing="0"
           filename="%s" fname="%s" ext="%s" path="%s" linkto="%s"
           fsize="%d" date="%d" fwidth="%d" fheight="%d" md5="%s" ><tr><td valign="bottom" align="center">
     <div class="imageBlock1">
      <div class="imageImage">
       <img src="%s" width="100" alt="%s" />
      </div>
      <div class="imageName">%s</div>
     </div>
    </td></tr></table>\n""" % (file, file, ext, linkto, linkto,
                               fsize, fdate, fwidth, fheight, md5_digest,
                               linkto, file, file)
    
    return ret

def UploadFile(request):
    #print request.POST
    top = request.POST['path']
    if top == '/': top = ''
    pathtype = request.POST['pathtype']
    
    if not isdir(STORAGE_ROOT + top + '.thumbs'):
        os.mkdir(STORAGE_ROOT + top + '.thumbs')
    
    files = Thumbs(top).load()
    
    # file uploaded from Flash multiload
    if (len(request.FILES)):
        for file in request.FILES.items():
            if -1 == file[1].name.rfind('.'):
                return HttpResponseForbidden()
            
            (name, ext) = file[1].name.rsplit('.', 2)
            if not ext in ALLOWED_IMAGES:
                return HttpResponseForbidden()
            
            file_body = file[1].read()
            md5_digest = md5.new(file_body).hexdigest()
            #print "md5: %s" % (md5_digest)
            
            #size = file[1].size
            #$files[$file]['imageinfo'] = getimagesize($_FILES['Filedata']['tmp_name']);
            filename = name + '.' + ext
            filelink = top + filename
            filepath = STORAGE_ROOT + top + filename
            
            img_file = open(filepath, 'wb')
            img_file.write(file_body)
            img_file.close()
            
            img_file = open(filepath, 'rb')
            image = Image.open(img_file)
            xsize, ysize = image.size
            img_file.close()
            
            # TODO: need to add support for unicode
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
            
            #files[filename]['general'] = info
    
    #print files
    Thumbs(top).dump(files)
    return HttpResponse('Ok.')

def generate_thumb(img, sizes, format):
    """
    Generates a thumbnail image and returns a ContentFile object with the thumbnail
    
    Parameters:
    ===========
    img         File object
    
    thumb_size  desired thumbnail size, ie: (200,120)
    
    format      format of the original image ('jpeg','gif','png',...)
                (this format will be used for the generated thumbnail, too)
    """
    
    img.seek(0) # see http://code.djangoproject.com/ticket/8222 for details
    image = Image.open(img)
    
    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGB', 'RGBA'):
        image = image.convert('RGB')
        
    # get size
    thumb_w, thumb_h = thumb_size
    # If you want to generate a square thumbnail
    if thumb_w == thumb_h:
        # quad
        xsize, ysize = image.size
        # get minimum size
        minsize = min(xsize,ysize)
        # largest square possible in the image
        xnewsize = (xsize-minsize)/2
        ynewsize = (ysize-minsize)/2
        # crop it
        image2 = image.crop((xnewsize, ynewsize, xsize-xnewsize, ysize-ynewsize))
        # load is necessary after crop                
        image2.load()
        # thumbnail of the cropped image (with ANTIALIAS to make it look better)
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    else:
        # not quad
        image2 = image
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    
    io = cStringIO.StringIO()
    # PNG and GIF are the same, JPG is JPEG
    if format.upper()=='JPG':
        format = 'JPEG'
    
    image2.save(io, format)
    return ContentFile(io.getvalue())




