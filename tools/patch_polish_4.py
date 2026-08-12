from pathlib import Path

home=Path('backend/_test_editorial_c_home.py')
s=home.read_text(encoding='utf-8')
s=s.replace('assert "day,day+6" in text\n','assert "todayDay,todayDay+6" in text\n')
home.write_text(s,encoding='utf-8')

map_test=Path('backend/_test_map_ux.py')
s=map_test.read_text(encoding='utf-8')
old='''    def test_cluster_and_nearby_share_activity_picker(self):
        self.assertEqual(self.html.count('id="activityPickerOverlay"'), 1)
        self.assertIn("function openActivityPicker({mode,items,title,sourceLocationId=null})", self.html)
        self.assertIn("openActivityPicker({mode:'cluster'", self.html)
        self.assertIn("openActivityPicker({mode:'nearby'", self.html)
        self.assertIn("zoomToBoundsOnClick:false,spiderfyOnMaxZoom:false", self.html)
        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("if(MOBILE_QUERY.matches)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
'''
new='''    def test_cluster_and_nearby_share_activity_picker(self):
        self.assertEqual(self.html.count('id="activityPickerOverlay"'), 1)
        self.assertIn("function openActivityPicker({mode,items,title,sourceLocationId=null})", self.html)
        self.assertIn("openActivityPicker({mode:'cluster'", self.html)
        self.assertIn("openActivityPicker({mode:'nearby'", self.html)
        self.assertIn("zoomToBoundsOnClick:false,spiderfyOnMaxZoom:false", self.html)
        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("venueIds.size===1&&eventIds.size>1", cluster_handler)
        self.assertIn("if(sameVenueMultiActivity)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
'''
if old not in s: raise RuntimeError('cluster picker legacy test mismatch')
s=s.replace(old,new,1)
old='''    def test_popup_metadata_and_empty_address_rules(self):
        popup_meta = self.html[self.html.index("function popupMetadataHtml"):self.html.index("function actionHtml")]
        self.assertIn("group.ip?", popup_meta)
        self.assertIn("group.organizer?", popup_meta)
        self.assertNotIn("licensor", popup_meta)
        app_js = self.html[self.html.index("const uiState="):]
        self.assertNotIn("地址未提供", app_js)
        self.assertNotIn("地點未提供", app_js)
        self.assertIn("FLOATING_ADDRESS_TEXT", app_js)
'''
new='''    def test_popup_metadata_and_empty_address_rules(self):
        compact = self.html[self.html.index("function mapCardHtml(group,location)"):self.html.index("function mobileCardHtml")]
        self.assertNotIn("popupMetadataHtml", compact)
        self.assertNotIn("group.ip", compact)
        self.assertNotIn("group.organizer", compact)
        self.assertIn("popupContextHtml", compact)
        self.assertIn("mapCardLocationHtml", compact)
        app_js = self.html[self.html.index("const uiState="):]
        self.assertNotIn("地址未提供", app_js)
        self.assertNotIn("地點未提供", app_js)
        self.assertIn("FLOATING_ADDRESS_TEXT", app_js)
'''
if old not in s: raise RuntimeError('popup metadata legacy test mismatch')
s=s.replace(old,new,1)
map_test.write_text(s,encoding='utf-8')
