from ....predicate import Predicate


class Number(Predicate):
    def __init__(self, value, definition="", tag="[NUMBER]"):
        """Initialize a Number object."""
        super().__init__(verbete=value, category="number", min_args=0, max_args=None, definition=definition)
        self.tag = tag

    def preval(self, annotated=False):
        """Evaluate the Number object."""
        if annotated:
            return f"{self.verbete}{self.tag}"
        return self.verbete

    def __add__(self, other):
        return other.__addpre__(self)

oîepé = Number("oîepé", definition="one, a single one", tag="[NUMBER:ONE]")
# mokõî1 (num.) - 1) dois (Fig., Arte, 4): mokõî apŷaba - dois homens (Anch., Arte, 9v); ...Mokõî nhõ abá rekoabane... - Duas, somente, serão as moradas das pessoas. (Ar, Cat.,163); 2) par, dupla de qualquer coisa (VLB, II, 64) ● mokõ-mokõî - de dois em dois, dois a dois (VLB, I, 106)
mokõî = Number("mokõî", definition="two, a pair, a couple", tag="[NUMBER:TWO]")
# mosapyr1 (num.) - três: Iîá mosapyr-y bé pekaî oîepegûasune. - Ainda bem que vós três, novamente, queimareis juntos. (Anch., Teatro, 50); Mosapyr o boîá... - Três de seus discípulos. (Ar., Cat., 52v); Mosapyr abá our. - Três pessoas vieram. (Anch., Arte, 9v) ● mosapy-sapyr - de três em três, três cada um (VLB, II, 136)
mosapyr = Number("mosapyr", definition="three, a trio", tag="[NUMBER:THREE]")
# oîoirundyk (ou oîeirundyk) (num.) - quatro: ...oîoirundyk îeapyká sykápe - no transcorrer de quatro gerações (Ar., Cat., 129)
oîoirundyk = Number("oîoirundyk", definition="four", tag="[NUMBER:FOUR]")
# ambó (etim. - esta mão) (num.) - cinco (Fig., Arte, 4)
ambó = Number("ambó", definition="five", tag="[NUMBER:FIVE]")
# amombokoty (num.) - cinco: -Îarekó bépe tekomonhangaba amõ Santa Madre Igreja remimonhanga? -Îarekó bé. -Mobype? -Amombokoty. -Temos também alguns mandamentos que a Santa Madre Igreja faz? -Temos. -Quantos? -Cinco. (Ar., Cat., 75)
amombokoty = Number("amombokoty", definition="five", tag="[NUMBER:FIVE]")
# moîepé1 (num.) - um: Opá kó mbó îabi'õ... moîepé me'enga Tupã potabamo. - A cada dez dar um como quinhão de Deus. (Ar., Cat., 78); 'Aretegûasu îabi'õ ã mundepora moîepé peîmosemukar ixébe îepi... - Eis que a cada Páscoa um prisioneiro fazeis-me libertar sempre. (Ar., Cat., 59v) [o mesmo que oîepé1 (v.)]
moîepé = Number("moîepé", definition="one, a single one", tag="[NUMBER:ONE]")
# oîeirundyk (num.) - quatro (o mesmo que oîoirundyk - v.) (Ar., Cat., 77)
oîeirundyk = Number("oîeirundyk", definition="four", tag="[NUMBER:FOUR]")
# xe-pó-xe-py (num.) - vinte (isto é, os dedos de meus pés e minhas mãos) (Fig., Arte, 4)
xe_pó_xe_py = Number("xe-pó-xe-py", definition="twenty (literally, the fingers of my feet and hands)", tag="[NUMBER:TWENTY]")
# moîerundyk (ou monherundyk) (num.) - quatro (Fig., Arte, 4): -Mbobype ybykûarusu yby apyterype sekóû...? -Moîerundyk. - Quantas furnas há no meio da terra? -Quatro. (Bettendorff, Compêndio, 48)
moîerundyk = Number("moîerundyk", definition="four", tag="[NUMBER:FOUR]")
# opambó (etim. - ambas as mãos) (num.) - dez (VLB, I, 102)
opambó = Number("opambó", definition="ten (literally, both hands)", tag="[NUMBER:TEN]")
# opakombó (etim. - ambas estas mãos) (num.) - dez (Fig., Arte, 4): Opakombó îabi'õ Tupã supé oîepé asé mba'e moîa'oka... - De cada dez, repartir uma de nossas coisas com Deus. (Ar., Cat., 78)
opakombó = Number("opakombó", definition="ten (literally, both these hands)", tag="[NUMBER:TEN]")
# mokõmokõîsyk (etim. - dois e dois no total) (num.) - quatro (VLB, I, 154)
mokõmokõîsyk = Number("mokõmokõîsyk", definition="four (literally, two and two in total)", tag="[NUMBER:FOUR]")
