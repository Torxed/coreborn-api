import psycopg2.extras
import ipaddress
import os
from typing import Union
from fastapi import FastAPI, Request
from pydantic import BaseModel, validator

from .database.postgresql import Database

app = FastAPI()
with open(f"{os.environ['CONFDIR']}/db.pw", 'r') as fh:
	db_password = fh.read()

db = Database(dbname='coreborn', user='coreborn', password=db_password, host='172.22.0.9')

db.query("""CREATE TABLE IF NOT EXISTS ip_addresses (id BIGSERIAL, ip INET NOT NULL UNIQUE, blocked BOOL)""")
db.query("""CREATE TABLE IF NOT EXISTS resources (id SERIAL, name VARCHAR NOT NULL UNIQUE, category VARCHAR NOT NULL, icon VARCHAR)""")
db.query("""CREATE TABLE IF NOT EXISTS positions (
	id BIGSERIAL,
	resource BIGINT NOT NULL,
	x DOUBLE PRECISION NOT NULL,
	y DOUBLE PRECISION NOT NULL,
	ip BIGINT NOT NULL,
	UNIQUE(resource, x, y))"""
)

colors = {
	'heartwood' : '#FF0000',
	'blushbell' : '#00FEB2',
	'dornwood' : '#0000FF',
	'ellyonwood' : '#D200FF',
	'gold' : '#FFD700',
	'ambrosite' : '#FFA500',
	'royalite' : '#008080',
	'sulfur' : '#f1dd38',
	'iron' : '#C2C2C2',
	'coal' : '#151716'
}

init_data = {
	'woodworking' : {
		'heartwood' : {
			'positions' : [
				[0.38099328572041335, 0.16579059361553822, 1],
				[0.3952967879146951, 0.18269473257241664, 1],
				[0.3855444000549575, 0.21195189615162927, 1],
				[0.38359392248301, 0.21910364724877013, 1],
				[0.590994704300095, 0.22105412482071762, 1],
				[0.5467838793359515, 0.23535762701499935, 1],
				[0.5558861080050399, 0.24771065163733358, 1],
				[0.5415826058107582, 0.2529119251625269, 1],
				[0.4778670051271396, 0.302974182842513, 1],
				[0.5597870631489349, 0.2802186111697921, 1],
				[0.5955458186346393, 0.2600636762596678, 1],
				[0.652109668221117, 0.25226176597187777, 1],
				[0.4200028371593635, 0.379692967339115, 1],
				[0.3907456735801509, 0.36929042028872827, 1],
				[0.37384153462327246, 0.36343898757288573, 1],
				[0.38489424086430835, 0.35498691809444655, 1],
				[0.5123254422315455, 0.4850187562242804, 1],
				[0.47396604998324454, 0.4772168459364904, 1],
				[0.3198783217993914, 0.414151404443521, 1],
				[0.30687513798640803, 0.37384153462327246, 1],
				[0.32768023208718144, 0.35758755485704324, 1],
				[0.3426338934721123, 0.3387329383282173, 1],
				[0.17294234471267908, 0.3387329383282173, 1]
			],
		},
		'blushbell' : {
			'positions' : [
				[0.17588726303122448, 0.16154184796130192, 1],
				[0.1790058315246859, 0.1964698150880699, 1],
				[0.19896466988283903, 0.19771724248545447, 1],
			],
		},
		'ellyonwood' : {
			'positions' : [
				[0.11725817535414965, 0.14719643289137935, 1],
				[0.2482380520795296, 0.13908815480837963, 1],
				[0.22141836303576132, 0.15468099727568677, 1],
				[0.32183626852521924, 0.15093871508353307, 1],
				[0.33493425619775724, 0.15717585207045592, 1],
				[0.10353647398291937, 0.29189801098798956, 1],
				[0.1708975534416862, 0.39605819866960124, 1],
				[0.15468099727568677, 0.39855305346437037, 1],
				[0.23389263700960702, 0.4022953356565241, 1],
				[0.22266579043314588, 0.4509450041545223, 1],
				[0.21580493974753073, 0.4652904192244449, 1],
				[0.21081523015799247, 0.4733986973074446, 1],
				[0.17713469042860905, 0.47838840689698287, 1],
				[0.30499599866052757, 0.48088326169175205, 1],
			],
		},
		'dornwood' : {
			'positions' : [
				[0.18087697262076277, 0.17339240823645533, 1],
				[0.1877378233063779, 0.1702738397429939, 1],
				[0.09667562329730424, 0.34678481647291065, 1],
				[0.4696564151152909, 0.2937691520840664, 1],
				[0.36986222332452523, 0.42911502470029234, 1],
			]
		}
	},
	'mining' : {
		'gold' : {
			'positions' : [
				[0.4004241945604472, 0.2002120972802236, 1],
				[0.3673673685297561, 0.13347473152014908, 1],
				[0.35239823976114126, 0.12910873562930308, 1],
				[0.30936199455137353, 0.19397496029330075, 1],
				[0.3106094219487581, 0.15156242878222534, 1],
				[0.295016579481451, 0.15031500138484077, 1],
				[0.27942373701414386, 0.1577995657691482, 1],
				[0.2588411849572984, 0.19709352878676217, 1],
				[0.255722616463837, 0.14033558220576423, 1],
				[0.2257843589266073, 0.13035616302668765, 1],
				[0.16902641234560933, 0.1284850219306108, 1],
				[0.16341298905737878, 0.1665315575508402, 1],
				[0.12723759453322622, 0.18649039590899333, 1],
				[0.10603132877768852, 0.12973244932799535, 1],
				[0.10603132877768852, 0.13534587261622594, 1],
				[0.10041790548945795, 0.16902641234560933, 1],
				[0.10166533288684251, 0.18524296851160876, 1],
				[0.16154184796130192, 0.21206265755537704, 1],
				[0.12037674384761107, 0.24137720139391444, 1],
				[0.11351589316199594, 0.2725628863285287, 1],
				[0.14657271919268708, 0.3424188205820647, 1],
				[0.09480448220122738, 0.44283672607152264, 1],
				[0.11413960686068822, 0.45905328223752206, 1],
				[0.15655213837176363, 0.42474902880944637, 1],
				[0.17463983563383992, 0.4141458959316775, 1],
				[0.1783821178259936, 0.4153933233290621, 1],
				[0.21455751235014617, 0.45842956853882977, 1],
				[0.299382575372297, 0.4378470164819843, 1],
				[0.4022953356565241, 0.4309861657963692, 1],
				[0.4640429918270603, 0.38233649729837094, 1],
				[0.5532340507400572, 0.2943928657827587, 1],
				[0.49398124936429, 0.25821747125860617, 1],
				[0.5232957932028275, 0.23389263700960702, 1],
				[0.585667163072056, 0.24137720139391444, 1],
				[0.6561468110242842, 0.25447518906645245, 1],
			]
		},
		'ambrosite' : {
			'positions' : [
				[0.2850371603023744, 0.47714097949959833, 1],
				[0.277552595918067, 0.4840018301852135, 1],
				[0.27505774112329784, 0.48025954799305975, 1],
				[0.264454608245529, 0.4733986973074446, 1],
				[0.2569700438612216, 0.4235016014120618, 1],
				[0.24449576988737587, 0.4309861657963692, 1],
				[0.24636691098345273, 0.4372233027832921, 1],
				[0.2507329068742987, 0.44470786716759947, 1],
				[0.24137720139391444, 0.44096558497544575, 1],
				[0.23576377810568389, 0.44657900826367636, 1],
				[0.23202149591353016, 0.45531100004536834, 1],
				[0.23264520961222246, 0.47589355210221373, 1],
				[0.21580493974753073, 0.47589355210221373, 1],
				[0.21143894385668474, 0.4615481370322912, 1],
				[0.21081523015799247, 0.4390944438793689, 1],
				[0.2014595246776082, 0.4515687178532146, 1],
				[0.18087697262076277, 0.4372233027832921, 1],
				[0.19896466988283903, 0.47838840689698287, 1],
				[0.18461925481291647, 0.47152755621136777, 1],
				[0.18212440001814734, 0.4702801288139832, 1],
				[0.18025325892207048, 0.47838840689698287, 1],
				[0.1708975534416862, 0.4702801288139832, 1],
				[0.12723759453322622, 0.4652904192244449, 1],
				[0.0979230506946888, 0.44096558497544575, 1],
				[0.10166533288684251, 0.4521924315519069, 1],
				[0.07734049863784338, 0.45468728634667605, 1],
				[0.06174765617053625, 0.4253727425081386, 1],
				[0.14719643289137935, 0.13846444110968736, 1],
				[0.14470157809661022, 0.14657271919268708, 1],
				[0.1490675739874562, 0.15156242878222534, 1],
				[0.1415830096031488, 0.17214498083907076, 1],
				[0.12287159864238022, 0.17463983563383992, 1],
				[0.12100045754630337, 0.17962954522337818, 1],
				[0.09729933699599652, 0.20270695207499276, 1],
				[0.09043848631038139, 0.1783821178259936, 1],
				[0.10790246987376537, 0.16341298905737878, 1],
				[0.10353647398291937, 0.1659078438521479, 1],
				[0.09355705480384281, 0.1540572835769945, 1],
				[0.0979230506946888, 0.13409844521884134, 1],
				[0.1110210383672268, 0.12599016713584166, 1],
				[0.13347473152014908, 0.13097987672537992, 1],
				[0.1365933000136105, 0.12723759453322622, 1],
				[0.14220672330184106, 0.12536645343714936, 1],
				[0.15031500138484077, 0.1284850219306108, 1],
				[0.15093871508353307, 0.13347473152014908, 1],
				[0.1584232794678405, 0.13160359042407221, 1],
				[0.15468099727568677, 0.13721701371230277, 1],
				[0.18087697262076277, 0.12536645343714936, 1],
				[0.17775840412730134, 0.12723759453322622, 1],
				[0.1783821178259936, 0.14220672330184106, 1],
				[0.1833718274155319, 0.14345415069922565, 1],
				[0.20333066577368503, 0.1322273041227645, 1],
				[0.20707294796583875, 0.1322273041227645, 1],
				[0.22266579043314588, 0.13160359042407221, 1],
				[0.225160645227915, 0.15592842467307136, 1],
				[0.23701120550306845, 0.1484438602887639, 1],
				[0.26694946304029815, 0.13409844521884134, 1],
				[0.2937691520840664, 0.19085639179983932, 1],
				[0.29065058359060497, 0.17463983563383992, 1],
				[0.2956402931801433, 0.1621655616599942, 1],
				[0.3118568493461427, 0.1496912876861485, 1],
				[0.3187177000317578, 0.14719643289137935, 1],
				[0.343042534280757, 0.14719643289137935, 1],
				[0.33618168359514183, 0.15156242878222534, 1],
				[0.3237074096212961, 0.1783821178259936, 1],
				[0.3112331356474504, 0.18960896440245475, 1],
			]
		},
		'royalite' : {
			'positions' : [
				[0.33618168359514183, 0.46341927812836803, 1],
				[0.3187177000317578, 0.4858729712812903, 1],
				[0.25260404797037556, 0.47838840689698287, 1],
				[0.21019151645930018, 0.4709038425126755, 1],
				[0.08981477261168909, 0.4640429918270603, 1],
				[0.08357763562476624, 0.46341927812836803, 1],
				[0.15655213837176363, 0.3935633438748321, 1],
				[0.14407786439791792, 0.3904447753813707, 1],
				[0.21892350824099216, 0.17463983563383992, 1],
				[0.13035616302668765, 0.15156242878222534, 1],
				[0.13534587261622594, 0.1708975534416862, 1],
				[0.1241190260397648, 0.1839955411142242, 1],
				[0.09355705480384281, 0.18711410960768562, 1],
				[0.09293334110515052, 0.1715212671403785, 1],
				[0.10478390138030394, 0.16777898494822477, 1],
				[0.10291276028422709, 0.13846444110968736, 1],
				[0.11476332055938052, 0.13160359042407221, 1],
				[0.14283043700053336, 0.14220672330184106, 1],
				[0.1584232794678405, 0.1359695863149182, 1],
				[0.19085639179983932, 0.13971186850707193, 1],
				[0.2008358109789159, 0.1284850219306108, 1],
				[0.20333066577368503, 0.13534587261622594, 1],
				[0.24387205618868357, 0.13347473152014908, 1],
				[0.2613360397520676, 0.13908815480837963, 1],
				[0.2681968904376827, 0.15093871508353307, 1],
				[0.30561971235921986, 0.15280985617960993, 1],
				[0.295016579481451, 0.18524296851160876, 1],
				[0.33805282469121867, 0.1702738397429939, 1],
			]
		},
		'sulfur' : {
			'positions' : [
				[0.18212440001814734, 0.47963583429436746, 1],
				[0.25759375755991387, 0.42973873839898463, 1],
				[0.2182997945422999, 0.4359758753859075, 1],
				[0.20769666166453105, 0.4004241945604472, 1],
				[0.1839955411142242, 0.4128984685342929, 1],
				[0.17651097672991675, 0.38358392469575553, 1],
				[0.1715212671403785, 0.4004241945604472, 1],
				[0.0979230506946888, 0.46341927812836803, 1],
				[0.12599016713584166, 0.44657900826367636, 1],
				[0.08295392192607395, 0.4147696096303698, 1],
				[0.09230962740645823, 0.3667436548310638, 1],
				[0.11351589316199594, 0.3436662479794492, 1],
				[0.10416018768161166, 0.32495483701868066, 1],
				[0.19771724248545447, 0.22453693152922274, 1],
				[0.1839955411142242, 0.1958461013893776, 1],
				[0.1715212671403785, 0.1883615370050702, 1],
				[0.11226846576461137, 0.21143894385668474, 1],
				[0.11975303014891879, 0.18586668221030103, 1],
				[0.10478390138030394, 0.14407786439791792, 1],
				[0.13160359042407221, 0.13409844521884134, 1],
				[0.19272753289591618, 0.13721701371230277, 1],
				[0.242624628791299, 0.15031500138484077, 1],
				[0.2257843589266073, 0.1540572835769945, 1],
				[0.3461611027742184, 0.13784072741099507, 1],
				[0.3405476794859878, 0.3330631151016804, 1],
				[0.3330631151016804, 0.3623776589402178, 1],
				[0.30437228496183527, 0.3760993603114481, 1],
				[0.32744969181344985, 0.47963583429436746, 1],
				[0.39980048086175496, 0.4235016014120618, 1],
				[0.39980048086175496, 0.31372799044221955, 1],
				[0.5301566438884425, 0.25385147536776015, 1],
				[0.5064555233381357, 0.33680539729383413, 1],
				[0.5675794658099798, 0.47152755621136777, 1],
			]
		},
		'iron' : {
			'positions' : [
				[0.40853247264344694, 0.2052018068697619, 1],
				[0.4235016014120618, 0.2388823465991453, 1],
				[0.39980048086175496, 0.24636691098345273, 1],
				[0.38607877949052466, 0.24449576988737587, 1],
				[0.35614052195329493, 0.24886176577822186, 1],
				[0.29002686989191273, 0.22765550002268417, 1],
				[0.30998570825006583, 0.22141836303576132, 1],
				[0.39668191236829353, 0.1715212671403785, 1],
				[0.3798416425036018, 0.1715212671403785, 1],
				[0.37235707811929436, 0.15468099727568677, 1],
				[0.36175394524152554, 0.16341298905737878, 1],
				[0.3436662479794492, 0.14782014659007164, 1],
				[0.329944546608219, 0.1534335698783022, 1],
				[0.3112331356474504, 0.15093871508353307, 1],
				[0.295016579481451, 0.17463983563383992, 1],
				[0.27817630961675927, 0.15904699316653279, 1],
				[0.23576377810568389, 0.1659078438521479, 1],
				[0.2638308945468367, 0.13285101782145678, 1],
				[0.22453693152922274, 0.1365933000136105, 1],
				[0.2133100849527616, 0.17651097672991675, 1],
				[0.21705236714491533, 0.1659078438521479, 1],
				[0.2176760808436076, 0.1496912876861485, 1],
				[0.20956780276060788, 0.15156242878222534, 1],
				[0.20707294796583875, 0.13971186850707193, 1],
				[0.1783821178259936, 0.13409844521884134, 1],
				[0.17651097672991675, 0.1278613082319185, 1],
				[0.16091813426260962, 0.13347473152014908, 1],
				[0.1621655616599942, 0.16029442056391735, 1],
				[0.1409592959044565, 0.15156242878222534, 1],
				[0.13035616302668765, 0.15530471097437906, 1],
				[0.12474273973845708, 0.13160359042407221, 1],
				[0.1234953123410725, 0.1284850219306108, 1],
				[0.10478390138030394, 0.13285101782145678, 1],
				[0.09729933699599652, 0.13784072741099507, 1],
				[0.12536645343714936, 0.14532529179530249, 1],
				[0.11413960686068822, 0.15156242878222534, 1],
				[0.13721701371230277, 0.1790058315246859, 1],
				[0.12224788494368793, 0.17962954522337818, 1],
				[0.12037674384761107, 0.17214498083907076, 1],
				[0.11039732466853451, 0.18212440001814734, 1],
				[0.10353647398291937, 0.19272753289591618, 1],
				[0.1883615370050702, 0.2182997945422999, 1],
				[0.2176760808436076, 0.21143894385668474, 1],
				[0.21081523015799247, 0.2264080726252996, 1],
				[0.2139337986514539, 0.23825863290045302, 1],
				[0.20208323837630046, 0.242624628791299, 1],
				[0.13534587261622594, 0.21206265755537704, 1],
				[0.15093871508353307, 0.23763491920176072, 1],
				[0.12661388083453393, 0.3405476794859878, 1],
				[0.14407786439791792, 0.3923159164774475, 1],
				[0.15468099727568677, 0.3916922027787552, 1],
				[0.15967070686522505, 0.39855305346437037, 1],
				[0.1708975534416862, 0.4141458959316775, 1],
				[0.18898525070376246, 0.4041664767526009, 1],
				[0.19771724248545447, 0.39792933976567807, 1],
				[0.2345163507082993, 0.3885736342852938, 1],
				[0.2257843589266073, 0.39605819866960124, 1],
				[0.21455751235014617, 0.39668191236829353, 1],
				[0.21954722193968446, 0.40666133154737005, 1],
				[0.24075348769522215, 0.4054139041499855, 1],
				[0.22391321783053045, 0.42038303291860035, 1],
				[0.10977361096984223, 0.44158929867413804, 1],
				[0.1365933000136105, 0.4565584274427529, 1],
				[0.15031500138484077, 0.44470786716759947, 1],
				[0.1752635493325322, 0.4353521616872152, 1],
				[0.16777898494822477, 0.44533158086629177, 1],
				[0.1833718274155319, 0.46279556442967573, 1],
				[0.19397496029330075, 0.4733986973074446, 1],
				[0.20956780276060788, 0.45343985894929145, 1],
				[0.21019151645930018, 0.4777646931982906, 1],
				[0.20707294796583875, 0.48088326169175205, 1],
				[0.23326892331091473, 0.46341927812836803, 1],
				[0.24137720139391444, 0.46591413292313716, 1],
				[0.260088612354683, 0.45593471374406064, 1],
				[0.26507832194422126, 0.4702801288139832, 1],
				[0.268820604136375, 0.47589355210221373, 1],
				[0.273186600027221, 0.4827544027878289, 1],
				[0.2831660192062976, 0.47526983840352144, 1],
				[0.28815572879583584, 0.4709038425126755, 1],
				[0.2869083013984513, 0.4496975767571378, 1],
				[0.29189801098798956, 0.4640429918270603, 1],
				[0.2981351479749124, 0.45406357264798375, 1],
				[0.30125371646837384, 0.4490738630584455, 1],
				[0.30437228496183527, 0.44470786716759947, 1],
				[0.30936199455137353, 0.45406357264798375, 1],
				[0.3068671397566044, 0.45593471374406064, 1],
				[0.3106094219487581, 0.46341927812836803, 1],
				[0.3062434260579121, 0.4815069753904443, 1],
				[0.33555796989644954, 0.4690327014165986, 1],
				[0.34803224387029524, 0.47963583429436746, 1],
				[0.2476143383808373, 0.3187177000317578, 1],
				[0.20707294796583875, 0.32245998222391153, 1],
				[0.2706917452324519, 0.30000628907098925, 1],
				[0.2956402931801433, 0.29065058359060497, 1],
				[0.3280734055121421, 0.29002686989191273, 1],
				[0.27443402742460554, 0.34678481647291065, 1],
				[0.299382575372297, 0.3318156877042958, 1],
				[0.3505270986650644, 0.3293208329095267, 1],
				[0.33992396578729556, 0.3293208329095267, 1],
				[0.3642488000362947, 0.32308369592260383, 1],
				[0.3773467877088327, 0.329944546608219, 1],
				[0.36050651784414095, 0.35177452606244897, 1],
				[0.3118568493461427, 0.3667436548310638, 1],
				[0.4041664767526009, 0.4621718507309835, 1],
				[0.4272438836042155, 0.4640429918270603, 1],
				[0.47215126991006, 0.44096558497544575, 1],
				[0.39481077127221664, 0.38233649729837094, 1],
				[0.4147696096303698, 0.36923850962583293, 1],
				[0.43285730689244606, 0.36175394524152554, 1],
				[0.47152755621136777, 0.3704859370232175, 1],
				[0.485249257582598, 0.2844134466036821, 1],
				[0.4964761041590592, 0.28877944249452814, 1],
				[0.5145638014211354, 0.29314543838537416, 1],
				[0.5120689466263663, 0.30437228496183527, 1],
				[0.520177224709366, 0.30998570825006583, 1],
				[0.5214246521067506, 0.31310427674352725, 1],
				[0.5314040712858271, 0.3199651274291424, 1],
				[0.5338989260805963, 0.3199651274291424, 1],
				[0.5532340507400572, 0.3237074096212961, 1],
				[0.542007204163596, 0.26195975345075984, 1],
				[0.546373200054442, 0.268820604136375, 1],
				[0.5326514986832117, 0.268820604136375, 1],
				[0.528909216491058, 0.1540572835769945, 1],
				[0.5513629096439803, 0.19148010549853162, 1],
				[0.6511571014347459, 0.19023267810114705, 1],
			]
		},
		'coal' : {
			'positions' : [
				[0.3654962274336792, 0.15280985617960993, 1],
				[0.3767230740101404, 0.15904699316653279, 1],
				[0.38545506579183236, 0.1621655616599942, 1],
				[0.3792179288049095, 0.17463983563383992, 1],
				[0.38171278359967864, 0.17713469042860905, 1],
				[0.38108906990098634, 0.1883615370050702, 1],
				[0.3779705014075249, 0.19522238769068534, 1],
				[0.37298079181798666, 0.19397496029330075, 1],
				[0.36861479592714064, 0.19459867399199304, 1],
				[0.3630013726389101, 0.19709352878676217, 1],
				[0.35925909044675636, 0.19958838358153133, 1],
				[0.1708975534416862, 0.20582552056845418, 1],
				[0.1715212671403785, 0.2133100849527616, 1],
				[0.21518122604883846, 0.21143894385668474, 1],
				[0.22079464933706902, 0.22266579043314588, 1],
				[0.2002120972802236, 0.23264520961222246, 1],
				[0.20395437947237732, 0.24075348769522215, 1],
				[0.21580493974753073, 0.23638749180437615, 1],
				[0.7054201932209748, 0.21518122604883846, 1],
				[0.7172707534961282, 0.22017093563837675, 1],
				[0.1790058315246859, 0.316846558935681, 1],
				[0.18025325892207048, 0.3536456671585258, 1],
				[0.17588726303122448, 0.34678481647291065, 1],
				[0.1584232794678405, 0.34927967126767984, 1],
				[0.16029442056391735, 0.34865595756898754, 1],
				[0.3798416425036018, 0.33930025208860326, 1],
				[0.3642488000362947, 0.329944546608219, 1],
				[0.36113023154283325, 0.32557855071737296, 1],
				[0.36050651784414095, 0.321212554826527, 1],
				[0.3499033849663721, 0.32495483701868066, 1],
				[0.3405476794859878, 0.32495483701868066, 1],
				[0.316846558935681, 0.308114567153989, 1],
				[0.31497541783960414, 0.32557855071737296, 1],
				[0.2981351479749124, 0.3330631151016804, 1],
				[0.3573879493506795, 0.3586353767480641, 1],
				[0.3174702726343733, 0.4016716219578318, 1],
				[0.2706917452324519, 0.36175394524152554, 1],
				[0.28004745071283615, 0.39543448497090894, 1],
				[0.27692888221937473, 0.38296021099706323, 1],
				[0.30125371646837384, 0.4135221822329852, 1],
				[0.31497541783960414, 0.41913560552121576, 1],
				[0.32308369592260383, 0.42038303291860035, 1],
				[0.3286971192108344, 0.4222541740146772, 1],
				[0.3548930945559104, 0.4178881781238312, 1],
				[0.38670249318921696, 0.41913560552121576, 1],
				[0.39917676716306266, 0.4309861657963692, 1],
				[0.40728504524606235, 0.43160987949506147, 1],
				[0.46778527401921405, 0.47651726580090603, 1],
				[0.47215126991006, 0.4478264356610609, 1],
				[0.4733986973074446, 0.44346043977021493, 1],
				[0.4621718507309835, 0.44221301237283034, 1],
				[0.51581122881852, 0.246990624682145, 1],
				[0.5145638014211354, 0.23950606029783758, 1],
				[0.5189297973119814, 0.26195975345075984, 1],
				[0.5538577644387495, 0.2638308945468367, 1],
				[0.5731928890982103, 0.2638308945468367, 1],
				[0.563837183617826, 0.2563463301625293, 1],
				[0.5869145904694405, 0.25260404797037556, 1],
				[0.5887857315655174, 0.264454608245529, 1],
				[0.5912805863602866, 0.27443402742460554, 1],
				[0.6442962507491308, 0.31248056304483496, 1],
				[0.6393065411595925, 0.3062434260579121, 1],
				[0.6311982630765928, 0.2981351479749124, 1],
				[0.6442962507491308, 0.28815572879583584, 1],
				[0.6505333877360536, 0.2856608740010667, 1],
				[0.6524045288321305, 0.2844134466036821, 1],
				[0.6193477028014394, 0.2837897329049899, 1],
				[0.6287034082818237, 0.27880002331545156, 1],
				[0.6386828274609002, 0.27630516852068243, 1],
				[0.6467911055439, 0.2725628863285287, 1],
				[0.6474148192425923, 0.25385147536776015, 1],
				[0.6461673918452077, 0.2476143383808373, 1],
				[0.6318219767752851, 0.2507329068742987, 1],
				[0.6143579932119011, 0.2563463301625293, 1],
				[0.6112394247184397, 0.24948547947691416, 1],
				[0.6124868521158242, 0.23701120550306845, 1],
				[0.6068734288275937, 0.24137720139391444, 1],
				[0.607497142526286, 0.22266579043314588, 1],
				[0.6062497151289014, 0.2133100849527616, 1],
				[0.590033158962902, 0.20707294796583875, 1],
				[0.5744403164955948, 0.22328950413183818, 1],
			]
		}
	}
}

db.query("INSERT INTO ip_addresses (ip, blocked) VALUES('127.0.0.1', false) ON CONFLICT DO NOTHING")
db.query("INSERT INTO ip_addresses (ip, blocked) VALUES('127.0.0.2', false) ON CONFLICT DO NOTHING")

with db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
	for category in init_data:
		for resource, values in init_data[category].items():
			db.query("INSERT INTO resources (name, category) VALUES(%s, %s) ON CONFLICT DO NOTHING", (resource, category))
			cur.executemany(
				"""
				INSERT INTO positions (resource, x, y, ip)
				VALUES(
					(SELECT id FROM resources WHERE name='""" + resource + """'), %s, %s, %s
				) ON CONFLICT DO NOTHING""",
				values['positions']
			)

def validate_resource(resource, allow_wildcard=False):
	if resource not in init_data and (allow_wildcard and resource != '*'):
		raise ValueError(f"Resource does not exist in resource list")

	return True

class Position(BaseModel):
	x: float
	y: float

	@validator('x', each_item=True)
	def validate_x(cls, v):
		if isinstance(v, float) and v > 0.0 and v < 1.0:
			return v
		raise ValueError(f"Position() is off the charts")

	@validator('y', each_item=True)
	def validate_y(cls, v):
		if isinstance(v, float) and v > 0.0 and v < 1.0:
			return v
		raise ValueError(f"Position() is off the charts")

@app.get("/api/resources/{resource}")
def read_root(resource :Union[str, None] = None):
	try:
		validate_resource(resource, allow_wildcard=True)
	except ValueError:
		return {'error': 'Unknown database error'}

	result = {}
	for category in {row['category'] for row in db.query("SELECT DISTINCT(category) FROM resources")}:
		result[category] = {}

		for resource in init_data[category]:
			result[category][resource] = {
				'icon' : None,
				'color' : colors[resource],
				'visible' : True,
				'positions' : db.query("""
					SELECT positions.x, positions.y FROM positions, ip_addresses, resources
					WHERE (positions.resource=resources.id AND resources.name=%s)
					  AND (positions.ip=ip_addresses.id AND ip_addresses.blocked='f')
					  AND (positions.resource=resources.id AND resources.category=%s)""", (resource, category), force_list=True)
			}

	return result

@app.put("/api/resources/{resource}")
def read_item(resource :str, pos :Position, request: Request):
	try:
		ipaddress.ip_address(request.client.host)
		validate_resource(resource)
	except ValueError:
		return {'error': 'Unknown database error'}

	db.query("INSERT INTO ip_addresses (ip, blocked) VALUES(%s, false) ON CONFLICT DO NOTHING", (request.client.host, ))
	ip_info = db.query("SELECT id, blocked FROM ip_addresses WHERE ip=%s", (request.client.host, ))

	if ip_info.get('blocked'):
		print("Blocked")
		return {'error': 'Unknown database error'}

	db.query("INSERT INTO positions (resource, x, y, ip) VALUES((SELECT id FROM resources WHERE name=%s), %s, %s, %s)", (resource, pos.x, pos.y, ip_info.get('id')))
	
	return {
		resource : {
			'icon' : None,
			'positions' : db.query("SELECT x, y FROM positions WHERE resource = (SELECT id FROM resources WHERE name=%s)", (resource, ), force_list=True)
		}
	}