mkdir -p berke0s/usr/local/bin \
&& cp BERKE0S.py berke0s/usr/local/bin/berke0s.py \
&& chmod +x berke0s/usr/local/bin/berke0s.py \
&& mkdir -p berke0s/usr/local/lib/python3.8/site-packages \
&& pip3 install --target=berke0s/usr/local/lib/python3.8/site-packages \
  flask pillow psutil requests numpy pandas \
  matplotlib pyglet pyopengl pyttsx3 pycairo \
  pyusb pyserial sounddevice pyalsa \
&& mksquashfs berke0s berke0s.tcz -noappend
