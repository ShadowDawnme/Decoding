# include <iostream>
# include <map>
# include <unordered_map>
using namespace std;
//  C++ type: C++ 17 standard language
// version 0.1. only support for string dictionary from python
std::unordered_map<std::string, std::string> StringDict_Flatten(std::unordered_map<string, std::unordered_map<string, string>> target){
    // here we start to iterate through the container
    std::unordered_map<string, string> result;
    string Key = target.begin()->first;
    std::unordered_map<string, string> repTartget = target.begin()->second;
    for (std::unordered_map<string, string> :: iterator iter = repTartget.begin(); iter != repTartget.end(); ++iter){
        string keys = Key + iter->first;
        string values = iter->second;
        result.emplace(keys, values);
    }
}

std::unordered_map<char[100], char[100]> StringList_Flatten(std::unordered_map<char[100], std::list<char[100]>> target){
    std::unordered_map<char[100], char[100]> res;
    // char *Key[100] = target.begin()->first;  // has problem
}  

int main(){
    string key1, key2;
    key1 = "A maintace";
    key2 = "function.";
    cout<< key1 + key2<<endl;
}