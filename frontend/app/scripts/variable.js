import Utils from "./utils";

const apiUrl = "https://" + window.location.host + "/api";
let userQuests, selfInfo, userRecipe, userMails;
let token = localStorage.getItem("jwt");
let refresh_token = localStorage.getItem("refresh_token");
const publicVapidKey = 'BBECmT60vswiNni3amDUVUQpgQiq7Sd5a-yqJf_Ues9q8mNy8SGlX7oyHD8vDjNRKqhwV8tMXVJWMrhmThKuqzQ';

function setToken(newToken) {
    token = newToken;
}

function getToken() {
    return token;
}

function setUserRecipe(newUserRecipe) {
    userRecipe = newUserRecipe;
}

function getUserRecipe() {
    return userRecipe;
}

function setRefreshToken(newToken) {
    refresh_token = newToken;
}

function getRefreshToken() {
    return refresh_token;
}

function setUserQuests(newUserQuests) {
    userQuests = newUserQuests;
}

function getUserQuests() {
    return userQuests;
}

function setSelfInfo(newSelfInfo) {
    selfInfo = newSelfInfo;
}

function getSelfInfo() {
    return selfInfo;
}

function setUserMails(newUserMails) {
    userMails = newUserMails;
}

function getUserMails() {
    return userMails;
}

const Variable = {
    apiUrl,
    setToken,
    getToken,
    publicVapidKey,
    setRefreshToken,
    getUserRecipe,
    setUserRecipe,
    getRefreshToken,
    setUserQuests,
    getUserQuests,
    setSelfInfo,
    getSelfInfo,
    setUserMails,
    getUserMails
}

export default Variable;
