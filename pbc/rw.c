#include<stdio.h>
#include<pbc/pbc.h>
#include<pbc/pbc_test.h>
#include<openssl/sha.h>

char param[1024];
int nm, dm;
char hash[20];
unsigned char hid[130];
element_t h, g, share, pks, pk ,pk_temp;
int n, t, f, ct = 0;
pairing_t pairing;

int main();

void init_pairing(){
  FILE *fp;
  int k, lk;
  fp = fopen("pairing", "r");
  size_t count = fread(param, 1, 1024, fp);
  fclose(fp);
  if(!count){
    pbc_die("input error\n");
    return;
  }
  pairing_init_set_buf(pairing, param, count);
  return;
}

int read_share(){
/*This function will open secrets and read the binary data into unsigned char
and store it in element share*/
  FILE *fp;
  unsigned char str[20];
  fp = fopen("../secrets","rb");
  if(!fp)
    return -1;
  fread(str, 20, 1, fp);
  fclose(fp);
  element_init_Zr(share, pairing);
  element_from_bytes(share, str);
}

void hash_id_s(char *str){
/*This function will read the string, hash it and then map to an element in G2.
It will then compute hash^share*/
  element_init_G2(h, pairing);
  element_init_G2(pks, pairing);
  SHA1(str, sizeof(str), hash);
  element_from_hash(h , hash, 20);
  element_pow_zn(pks, h, share);
}

int lambda(int i, int ei){
/*
*/
  int j;
  nm = 1;
  dm = 1;
  for(j = 1; j <= ei; j++){
    if(j==i)
      continue;
    nm *= j;
    dm *= j - i;
  }
  return 1;
}

void gen_privatekey(unsigned char *str, int nodeID, int senderID){
/*This will compute the private key from all the IBC_REPLY's received
*/
  int i, j;
   i = 1;
  signed long int num, dnum;
  
  num = (long)nm;
  dnum = (long)dm;
  
  lambda(2, 1, 10);
  element_t b, c, ci, keyshare;
  
  element_init_Zr(b, pairing);
  element_init_Zr(c, pairing);
  element_init_Zr(ci, pairing);

  element_init_G2(keyshare, pairing);
  element_init_G2(pk_temp, pairing);
  element_init_G2(pk, pairing);
  
  element_set_si(b, nm);
  element_set_si(c, dm);
  
  printf("num and dnum\n%li %li %d %d\n",num, dnum, nm, dm);

  element_printf("b\n%B\n", b);
  element_printf("c\n%B\n", c);
  int asd;
  element_from_bytes(keyshare, str);
  asd = element_length_in_bytes(keyshare);
  element_printf("DKG share is %d bytes\n%B\n", asd, keyshare);

  element_pow_zn(pk_temp, keyshare, b);
  asd = element_length_in_bytes(pk_temp);
  element_printf("pk_temp is %d bytes\n%B\n", asd, pk_temp);

  element_invert(ci, c);
  asd = element_length_in_bytes(ci);
  element_printf("ci is %d bytes\n%B\n", asd, ci);

  element_pow_zn(pk_temp, pk_temp, ci);
  asd = element_length_in_bytes(pk_temp);
  element_printf("pk_temp is %d bytes\n%B\n", asd, pk_temp);
  
  element_mul(pk, pk, pk_temp);
  asd = element_length_in_bytes(pk);
  element_printf("pk is %d bytes\n%B\n", asd, pk);
}

int main(){
  char asd[20];
  unsigned char key[100];
  init_pairing(1, 1, 1);
  read_share();
  printf("Give a string to encrypt : ");
  scanf("%s", asd);
  hash_id_s(asd);
  element_printf("The string has been hashed, it is : %B\n", pks);
  element_to_bytes(hid, key);
  gen_privatekey(key, 1, 2);
  //element_printf("The string is :\n%B\n", pk);
  return 0;
}