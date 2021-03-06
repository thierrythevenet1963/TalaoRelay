import didkit
import json
from jwcrypto import jwk
import logging
logging.basicConfig(level=logging.INFO)
from .helpers import ethereum_to_jwk256kr, ethereum_pvk_to_address, ethereum_to_jwk256k




def sign(credential, pvk, did, rsa=None):
    """ sign credential for did:ethr, did:tz, did:web

    @method is str
        ethr (default method) -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 with "alg" :"ES256K-R"
        web  -> curve secp256k1 with "alg" :"ES256K" or RSA

    @credential is dict
    return is str

    """
    method = did.split(':')[1]
    if method == 'web' and not rsa :
        key = ethereum_to_jwk256k(pvk)
        vm = did + "#key-1"

    elif method == 'web' and rsa :
        key = jwk.JWK.from_pem(rsa.encode())
        key = key.export_private()
        #del key['kid']
        vm = did + "#key-2"

    else :
        logging.error('method not supported')
        return None

    logging.info('key = %s', key)
    logging.info('did = %s', did)
    logging.info('vm = %s', vm)

    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm
    }
    return didkit.issueCredential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     key)


def verify (credential) :
    """
    credential  str
    return list
    """
    try :
        result = didkit.verifyCredential(credential, '{}')
    except:
        return "Failed : JSON-LD malformed"

    if not json.loads(result)['errors'] :
        return "Signature verified : "
    else :
        return "Signature rejected : " + result
